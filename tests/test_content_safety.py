"""No weapons, no secrets, no real-world identifiers, and no data leaking across the tenant boundary."""

import re
from pathlib import Path

import pytest

from generator.config import ROOT
from generator.kdy.world import ISOLATION_FACTS
from tests.textract import normalize

BANNED = re.compile("|".join([
    r"\bweapons?\b", r"superlaser", r"turbolaser", r"laser cannon", r"ion cannon", r"\bblasters?\b", r"\bkyber\b", r"tractor beam",
    r"\bdetention\b", r"exhaust port", r"death star", r"battle station", r"star destroyer", r"stormtrooper", r"\btorpedo", r"\bmissiles?\b",
    r"\bbombs?\b", r"\bexplosives?\b", r"\bammunition\b", r"\bguns?\b", r"\bkill(ed|ing|s)?\b", r"\bviolen(ce|t)\b", r"\bespionage\b",
    r"\bspy\b", r"\bspies\b", r"\brebels?\b", r"\bdefect(ed|ion|or|ors)\b", r"\binsider\b", r"\bsecrets?\b", r"\bclassified\b",
    r"\bpasswords?\b", r"\bpasscodes?\b", r"access codes?", r"\bmilitary\b", r"\barmy\b", r"\bnavy\b", r"\badmiral\b", r"\bcolonel\b",
    r"\blieutenant\b", r"\bpalpatine\b", r"\bvader\b", r"\btarkin\b", r"\bkrennic\b", r"\berso\b", r"\bmotti\b", r"\btagge\b",
    r"\byularen\b", r"\bbodhi\b", r"\bveers\b",
]), re.IGNORECASE)
CASE_SENSITIVE_BANNED = re.compile(r"\bTIE\b")

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
SSN_LIKE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# Card-number shapes: 13-19 contiguous digits, or four-digit groups separated by spaces or dashes.
CARD_LIKE = re.compile(r"\b\d{13,19}\b|\b(?:\d{4}[ -]){3}\d{1,7}\b")
SECRET_LIKE = re.compile(r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|\bsk-[A-Za-z0-9]{20,}|\bghp_[A-Za-z0-9]{20,}|\bxox[abp]-")


def _luhn(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char) * (2 if index % 2 else 1)
        total += value - 9 if value > 9 else value
    return total % 10 == 0


@pytest.fixture(scope="module")
def corpus(dataset) -> dict[str, list[tuple[str, str]]]:
    """(name, text) of every readable file, per tenant, plus the ground truth and the generator source."""
    texts: dict[str, list[tuple[str, str]]] = {"empire": [], "kdy": []}
    for document_id, document in dataset.documents().items():
        text = dataset.text(document_id)
        if text:
            texts[document["tenant"]].append((document["object_key"], text))
    for tenant in texts:
        for csv_file in sorted((dataset.seed_root / tenant).glob("*.csv")):
            texts[tenant].append((csv_file.name, normalize(csv_file.read_text(encoding="utf-8"))))
    texts["other"] = [(p.name, p.read_text(encoding="utf-8")) for p in sorted(dataset.ground_truth.iterdir())]
    texts["other"] += [(str(p.relative_to(ROOT)), p.read_text(encoding="utf-8")) for p in sorted(Path(ROOT, "generator").rglob("*.py"))]
    return texts


def test_no_weapons_secrets_or_star_wars_characters(corpus):
    hits = [f"{name}: {match.group(0)!r}" for texts in corpus.values() for name, text in texts
            for match in [*BANNED.finditer(text), *CASE_SENSITIVE_BANNED.finditer(text)]]
    assert not hits, "\n".join(hits[:40])


def test_email_addresses_use_reserved_example_domains(corpus):
    bad = sorted({domain for texts in corpus.values() for _, text in texts for domain in EMAIL.findall(text)
                  if not domain.rstrip(".").endswith(".example")})
    assert not bad, bad


def test_no_real_format_identifiers_or_credentials(corpus):
    hits = []
    for texts in corpus.values():
        for name, text in texts:
            hits += [f"{name}: SSN-like {m.group(0)}" for m in SSN_LIKE.finditer(text)]
            hits += [f"{name}: card-like {m.group(0)}" for m in CARD_LIKE.finditer(text) if _luhn(re.sub(r"\D", "", m.group(0)))]
            hits += [f"{name}: credential-like {m.group(0)}" for m in SECRET_LIKE.finditer(text)]
    assert not hits, "\n".join(hits[:40])


def test_kdy_internal_facts_never_reach_the_empire_tenant(corpus):
    leaks = [f"{name}: {fact}" for name, text in corpus["empire"] for fact in ISOLATION_FACTS.values() if fact in text]
    assert not leaks, leaks
    assert all(any(fact in text for _, text in corpus["kdy"]) for fact in ISOLATION_FACTS.values())


def test_empire_facts_asked_by_kdy_users_are_not_in_the_kdy_tenant(dataset, corpus):
    forbidden = {value for q in dataset.json("questions.json") if q["pool"] == "kdy:isolation-kdy-asks" for value in q["expected"]["must_not_include"]}
    assert forbidden
    leaks = [f"{name}: {value}" for name, text in corpus["kdy"] for value in forbidden if value in text]
    assert not leaks, leaks
