"""The generator is deterministic: a fresh build reproduces the dataset byte for byte."""

import io
from datetime import date

from PIL import Image

from generator.build import build
from generator.docs.model import Doc, ScannedPages, Sheet
from generator.docs.render import render

SAMPLE_BLOCKS = [
    ("h1", "Heading"), ("p", "Paragraph with ümlauts and ±2%."), ("bullets", ["one", "two"]), ("numbered", ["first"]),
    ("table", ["A", "B"], [["1", "2"]]), ("kv", [("Key", "Value")]), ("note", "A note."), ("hidden", "Hidden text."), ("pagebreak",),
]


def _doc(fmt: str, content) -> Doc:
    return Doc(doc_number="T-1", title="Sample", doc_type="TEST", fmt=fmt, key=f"t.{fmt}", label="INTERNAL",
               created_date=date(2026, 1, 2), content=content, company="Empire Incorporated")


def test_every_renderer_is_deterministic():
    samples = {
        "md": SAMPLE_BLOCKS, "pdf": SAMPLE_BLOCKS, "docx": SAMPLE_BLOCKS,
        "xlsx": [Sheet("One", [["a", 1], ["b", 2.5]]), Sheet("Two", [["x"]], hidden=True)],
        "csv": [["a", "b"], [1, 2]], "json": {"a": [1, 2], "day": date(2026, 1, 2)},
    }
    for fmt, content in samples.items():
        assert render(_doc(fmt, content)) == render(_doc(fmt, content)), fmt


def test_scans_render_deterministically():
    buffer = io.BytesIO()
    Image.new("L", (40, 60), 200).save(buffer, format="JPEG")
    scan = ScannedPages([buffer.getvalue()])
    assert render(_doc("pdf", scan)) == render(_doc("pdf", scan))


def test_a_fresh_build_reproduces_the_committed_checksums(dataset, tmp_path):
    build(tmp_path)
    expected = (dataset.root / "checksums.sha256").read_text(encoding="utf-8")
    actual = (tmp_path / "checksums.sha256").read_text(encoding="utf-8")
    if actual != expected:
        expected_lines, actual_lines = set(expected.splitlines()), set(actual.splitlines())
        changed = sorted(line.split("  ", 1)[1] for line in expected_lines ^ actual_lines)
        raise AssertionError(f"{len(changed)} files differ, e.g. {changed[:10]}")
