"""The generated dataset has the promised shape: tenants, people, formats, languages and size."""

import hashlib
from collections import Counter

from generator.config import EMPIRE_HEADCOUNT, KDY_HEADCOUNT
from generator.labels import LABELS

FORMATS = {"md", "pdf", "docx", "xlsx", "csv", "json", "svg", "png", "eml", "ics"}
MAX_BYTES = 100 * 1024 * 1024


def test_every_file_is_registered_with_its_size_and_hash(dataset):
    documents = dataset.documents()
    registered = {dataset.path(d) for d in documents.values()}
    on_disk = {p for p in dataset.bucket_root.rglob("*") if p.is_file()}
    assert on_disk == registered
    for document in documents.values():
        data = dataset.path(document).read_bytes()
        assert len(data) == int(document["size_bytes"]), document["document_id"]
        assert hashlib.sha256(data).hexdigest() == document["sha256"], document["document_id"]


def test_two_tenants_with_their_own_buckets(dataset):
    buckets = Counter((d["tenant"], d["bucket"]) for d in dataset.documents().values())
    assert set(buckets) == {("empire", "empire-inc-engineering"), ("kdy", "kdy-engineering")}
    assert buckets[("empire", "empire-inc-engineering")] > 2000
    assert buckets[("kdy", "kdy-engineering")] > 100


def test_headcounts(dataset):
    empire = Counter(row["status"] for row in dataset.table("empire", "employees"))
    kdy = Counter(row["status"] for row in dataset.table("kdy", "employees"))
    assert empire["ACTIVE"] == EMPIRE_HEADCOUNT and empire["DEPARTED"] > 0
    assert kdy["ACTIVE"] == KDY_HEADCOUNT


def test_formats_labels_and_languages(dataset):
    empire = [d for d in dataset.documents().values() if d["tenant"] == "empire"]
    assert {d["format"] for d in empire} >= FORMATS
    assert {d["sensitivity"] for d in empire} == set(LABELS)
    german = sum(1 for d in empire if d["language"] == "de") / len(empire)
    assert 0.08 <= german <= 0.16, f"German share {german:.1%}"


def test_total_size_stays_under_100_mb(dataset):
    total = sum(p.stat().st_size for folder in (dataset.bucket_root, dataset.seed_root, dataset.ground_truth) for p in folder.rglob("*") if p.is_file())
    assert total < MAX_BYTES, f"{total / 1e6:.1f} MB"
