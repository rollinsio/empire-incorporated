"""The ground truth is complete, consistent and grounded in the generated data."""

import csv
from collections import Counter

import pytest

from generator.labels import LABELS, RANK, may_see
from tests.textract import normalize

REQUIRED_CATEGORIES = {
    "lookup": 40, "cross_source": 20, "temporal": 20, "approved_revision": 6, "tenant_isolation": 8,
    "no_answer": 8, "injection": 8, "mislabeled": 12, "access_control": 10,
}


@pytest.fixture(scope="module")
def questions(dataset):
    return dataset.json("questions.json")


@pytest.fixture(scope="module")
def manifest(dataset):
    return dataset.json("manifest.json")


@pytest.fixture(scope="module")
def logins(dataset):
    return {login["username"]: {**login, "tenant": tenant} for tenant, info in dataset.json("logins.json").items() for login in info["logins"]}


def _rows(dataset, source: dict) -> list[dict]:
    if source["kind"] == "view":
        return dataset.view_rows(source["tenant"], source["view"], source["key"])
    return dataset.rows(source["tenant"], source["table"], source["key"])


def _haystack(dataset, source: dict) -> str:
    if source["kind"] == "document":
        if source.get("requires_ocr"):
            return normalize(source["ocr_text"])
        return dataset.text(source["document_id"]) or ""
    return normalize(" | ".join(" | ".join(row.values()) for row in _rows(dataset, source)))


def _ungrounded(dataset, questions: list[dict]) -> list[str]:
    """Every must_include string that appears in none of its question's sources."""
    failures = []
    for q in questions:
        if q["expected"]["type"] not in ("answer", "decline_instruction"):
            continue
        haystacks = [_haystack(dataset, s) for s in q["sources"]]
        for needle in q["expected"]["must_include"]:
            if not any(normalize(needle) in haystack for haystack in haystacks):
                failures.append(f"{q['id']} {q['pool']}: {needle!r} not in {[s.get('uri') or s.get('table') or s.get('view') for s in q['sources']]}")
    return failures


def test_every_required_category_is_covered(questions):
    counts = Counter(q["category"] for q in questions)
    for category, minimum in REQUIRED_CATEGORIES.items():
        assert counts[category] >= minimum, f"{category}: {counts[category]} < {minimum}"


def test_question_ids_are_unique_and_logins_exist(questions, logins):
    assert len({q["id"] for q in questions}) == len(questions)
    for q in questions:
        assert q["asked_as"] in logins, q["id"]
        assert logins[q["asked_as"]]["tenant"] == q["tenant"], q["id"]


def test_every_source_exists(dataset, questions, manifest):
    documents = dataset.documents()
    sources = [s for q in questions for s in q["sources"]] + [s for m in manifest for s in m["locations"]]
    for source in sources:
        if source["kind"] == "document":
            document = documents[source["document_id"]]
            assert document["tenant"] == source["tenant"]
            assert f"s3://{document['bucket']}/{document['object_key']}" == source["uri"]
            assert dataset.path(document).exists()
        else:
            assert _rows(dataset, source), source


def test_answers_are_grounded_in_their_sources(dataset, questions):
    """Every must_include string appears verbatim in at least one cited source."""
    failures = _ungrounded(dataset, questions)
    assert not failures, "\n".join(failures[:40])


def test_scenarios_ask_every_slot_once_and_are_grounded(dataset, logins):
    scenarios = dataset.json("scenarios.json")
    slots = list(scenarios["slots"])
    prompts = [p for s in scenarios["scenarios"] for p in s["prompts"]]
    assert len(scenarios["scenarios"]) == 6
    for scenario in scenarios["scenarios"]:
        assert [p["slot"] for p in scenario["prompts"]] == slots, scenario["id"]
    assert len({p["question"] for p in prompts}) == len(prompts)
    for p in prompts:
        assert p["asked_as"] in logins, p["id"]
        assert (p["expected"]["type"] == "answer") == (p["slot"] != "boundary"), p["id"]
        if p["slot"] == "german":
            assert any(s.get("language") == "de" for s in p["sources"]), p["id"]
        if p["slot"] == "database":
            assert all(s["kind"] in ("table", "view") for s in p["sources"]), p["id"]
        if p["slot"] == "person":
            assert "name" in p["pii"]["in_answer"], p["id"]
    failures = _ungrounded(dataset, prompts)
    assert not failures, "\n".join(failures)


def test_expected_outcome_matches_the_askers_access(questions, logins):
    for q in questions:
        level = logins[q["asked_as"]]["access_level"]
        required = max((s.get("true_sensitivity") or s.get("sensitivity") for s in q["sources"]), key=RANK.get, default="PUBLIC")
        if q["expected"]["type"] == "answer":
            assert may_see(level, required), q["id"]
        if q["expected"]["type"] == "refuse":
            assert not may_see(level, required), q["id"]


def test_refusals_and_isolation_do_not_cite_forbidden_values_as_answers(questions):
    for q in questions:
        if q["expected"]["type"] in ("refuse", "not_found") and q["category"] in ("tenant_isolation", "mislabeled", "access_control"):
            assert q["expected"]["answer"] is None, q["id"]
            assert q["expected"]["must_not_include"], q["id"]


def test_tenant_isolation_questions_have_no_sources_in_the_askers_tenant(questions):
    for q in questions:
        if q["category"] == "tenant_isolation" and q["expected"]["type"] == "not_found":
            assert all(s["tenant"] != q["tenant"] for s in q["sources"]), q["id"]


def test_manifest_items(manifest, dataset):
    documents = dataset.documents()
    ids = [m["id"] for m in manifest]
    assert len(ids) == len(set(ids))
    by_category = Counter(m["category"] for m in manifest)
    assert by_category["mislabeled"] >= 5 and by_category["injection"] >= 6 and by_category["approved_revision"] >= 5
    for item in manifest:
        if item["category"] == "mislabeled":
            for location in item["locations"]:
                document = documents[location["document_id"]]
                assert RANK[document["sensitivity"]] < RANK[item["true_sensitivity"]], item["id"]
        if item["category"] == "approved_revision":
            statuses = Counter(location["approval_status"] for location in item["locations"])
            assert statuses["APPROVED"] == 1 and len(item["locations"]) >= 2, item["id"]
        if item["category"] == "injection":
            assert normalize(item["description"]) in dataset.text(item["locations"][0]["document_id"]), item["id"]


def test_access_matrix_covers_every_document(dataset, logins):
    with open(dataset.ground_truth / "access_matrix.csv", newline="", encoding="utf-8") as handle:
        header, *rows = list(csv.reader(handle))
    assert header[5:] == list(logins)
    assert sorted(row[0] for row in rows) == sorted(dataset.documents())
    assert {cell for row in rows for cell in row[5:]} == {"allow", "deny", "mislabeled"}


def test_labels_are_known(dataset):
    assert {d["sensitivity"] for d in dataset.documents().values()} == set(LABELS)
