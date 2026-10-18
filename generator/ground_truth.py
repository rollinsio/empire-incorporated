"""Write ``ground_truth/``: the test manifest, the test logins, the access matrix and the questions.

Builders offer far more questions than an evaluation needs. Pools of ordinary
questions are sampled down to ``POOL_LIMIT`` each; every question about a
planted test case is kept. A question without an explicit ``asked_as`` is
asked by the lowest login of its tenant that may see all of its sources.
"""

import csv
import io
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from generator.config import AS_OF, EMPIRE_BUCKET, EMPIRE_DATABASE, KDY_BUCKET, KDY_DATABASE
from generator.docs.model import DocumentStore
from generator.labels import DESCRIPTIONS, INTERNAL, LABELS, RANK, may_see
from generator.rand import stream
from generator.truth import QUESTION_CATEGORIES, Collector

POOL_LIMIT = 4
KEEP_ALL = ("approved_revision", "tenant_isolation", "no_answer", "injection", "mislabeled")
TENANTS = {
    "empire": {"company": "Empire Incorporated", "database": EMPIRE_DATABASE, "schema": "empire", "bucket": EMPIRE_BUCKET},
    "kdy": {"company": "Kuat Drive Yards", "database": KDY_DATABASE, "schema": "kdy", "bucket": KDY_BUCKET},
}


def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"not JSON serializable: {type(value)}")


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=_json_default) + "\n", encoding="utf-8")


def tenant_of(username: str) -> str:
    return "kdy" if username.startswith("kdy.") else "empire"


def _required_level(sources: list[dict]) -> str:
    """The lowest label that may see every source; questions without sources are asked by an ordinary employee."""
    if not sources:
        return INTERNAL
    levels = []
    for source in sources:
        if source["kind"] == "document":
            levels += [source["label"], source["true_sensitivity"]]
        else:
            levels.append(source["sensitivity"])
    return max(levels, key=RANK.get)


class _Logins:
    def __init__(self, logins: dict[str, list[dict]]):
        self.by_name = {login["username"]: login for tenant_logins in logins.values() for login in tenant_logins}
        self.by_level = {(tenant, login["access_level"]): login["username"] for tenant, tenant_logins in logins.items() for login in tenant_logins}

    def level(self, username: str) -> str:
        return self.by_name[username]["access_level"]

    def for_level(self, tenant: str, level: str) -> str:
        return self.by_level[(tenant, level)]


def _resolve(question: dict, logins: _Logins) -> dict:
    """Fill in who asks, and check that the expected outcome matches what that login may see."""
    expected = question["expected"]["type"]
    sources = question["sources"]
    asked_as = question["asked_as"] or logins.for_level(question["tenant"], _required_level(sources))
    tenant = tenant_of(asked_as)
    same_tenant = [s for s in sources if s["tenant"] == tenant]
    if expected == "answer":
        assert sources and len(same_tenant) == len(sources), question["question"]
        assert may_see(logins.level(asked_as), _required_level(sources)), (asked_as, question["question"])
    elif expected == "refuse":
        assert not may_see(logins.level(asked_as), _required_level(sources)), (asked_as, question["question"])
    return {**question, "tenant": tenant, "asked_as": asked_as}


def select_questions(collector: Collector, logins: _Logins) -> list[dict]:
    rng = stream("ground-truth")
    pools: dict[str, list[dict]] = {}
    for question in collector.offered_questions:
        pools.setdefault(question["pool"], []).append(question)
    chosen = []
    for pool in sorted(pools):
        offered = pools[pool]
        keep = offered if offered[0]["category"] in KEEP_ALL or len(offered) <= POOL_LIMIT else rng.sample(offered, POOL_LIMIT)
        chosen += [_resolve(q, logins) for q in keep]
    chosen.sort(key=lambda q: (QUESTION_CATEGORIES.index(q["category"]), q["pool"]))
    return [{"id": f"Q-{n:04d}", **{k: v for k, v in q.items() if k != "pool"}, "pool": q["pool"]} for n, q in enumerate(chosen, start=1)]


def _access_matrix(stores: dict[str, DocumentStore], logins: dict[str, list[dict]]) -> bytes:
    usernames = [(tenant, login["username"], login["access_level"]) for tenant, tenant_logins in logins.items() for login in tenant_logins]
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["document_id", "tenant", "uri", "label", "true_sensitivity"] + [name for _, name, _ in usernames])
    for tenant, store in stores.items():
        for doc in store.docs:
            cells = []
            for login_tenant, _, level in usernames:
                if login_tenant != tenant or not may_see(level, doc.label):
                    cells.append("deny")
                elif not may_see(level, doc.true_sensitivity):
                    cells.append("mislabeled")
                else:
                    cells.append("allow")
            writer.writerow([doc.document_id, tenant, store.uri(doc), doc.label, doc.true_sensitivity] + cells)
    return buffer.getvalue().encode("utf-8")


def _summary(stores: dict[str, DocumentStore], questions: list[dict], manifest: list[dict]) -> dict:
    summary = {"as_of": AS_OF, "tenants": {}}
    for tenant, store in stores.items():
        docs = store.docs
        summary["tenants"][tenant] = {
            **TENANTS[tenant],
            "documents": len(docs),
            "bytes": sum(d.size_bytes for d in docs),
            "german_documents": sum(1 for d in docs if d.language == "de"),
            "by_label": dict(sorted(Counter(d.label for d in docs).items(), key=lambda kv: LABELS.index(kv[0]))),
            "by_format": dict(sorted(Counter(d.fmt for d in docs).items())),
            "by_type": dict(sorted(Counter(d.doc_type for d in docs).items())),
        }
    summary["questions"] = {
        "total": len(questions),
        "by_category": {c: n for c in QUESTION_CATEGORIES if (n := sum(1 for q in questions if q["category"] == c))},
        "by_expected_type": dict(sorted(Counter(q["expected"]["type"] for q in questions).items())),
        "by_tenant": dict(sorted(Counter(q["tenant"] for q in questions).items())),
    }
    summary["manifest"] = {"total": len(manifest), "by_category": dict(sorted(Counter(m["category"] for m in manifest).items()))}
    return summary


def write(out_dir: Path, collector: Collector, stores: dict[str, DocumentStore], logins: dict[str, list[dict]]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    questions = select_questions(collector, _Logins(logins))
    _write_json(out_dir / "questions.json", questions)
    _write_json(out_dir / "manifest.json", collector.manifest)
    _write_json(out_dir / "logins.json", {
        tenant: {**TENANTS[tenant], "logins": [{**login, "may_see": [label for label in LABELS if may_see(login["access_level"], label)],
                                                "label_descriptions": {label: DESCRIPTIONS[label] for label in LABELS}} for login in tenant_logins]}
        for tenant, tenant_logins in logins.items()
    })
    (out_dir / "access_matrix.csv").write_bytes(_access_matrix(stores, logins))
    summary = _summary(stores, questions, collector.manifest)
    _write_json(out_dir / "summary.json", summary)
    return summary
