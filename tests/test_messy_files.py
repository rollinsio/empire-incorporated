"""Every messy file is messy in the way the manifest says."""

import io
from collections import Counter

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader


@pytest.fixture(scope="module")
def messy(dataset) -> list[tuple[dict, dict, bytes]]:
    documents = dataset.documents()
    items = []
    for item in dataset.json("manifest.json"):
        if item["category"] == "messy":
            document = documents[item["locations"][0]["document_id"]]
            items.append((item, document, dataset.path(document).read_bytes()))
    return items


def _of_kind(messy, kind):
    found = [(item, document, data) for item, document, data in messy if item["kind"] == kind]
    assert found, kind
    return found


def test_every_kind_is_present(messy):
    kinds = Counter(item["kind"] for item, _, _ in messy)
    assert set(kinds) == {"scanned", "multi_sheet", "long_document", "empty", "corrupt", "wrong_extension", "legacy_encoding", "duplicate", "odd_name"}


def test_scans_are_image_only(messy):
    for item, _, data in _of_kind(messy, "scanned"):
        reader = PdfReader(io.BytesIO(data))
        assert all(not (page.extract_text() or "").strip() for page in reader.pages), item["id"]
        assert item["locations"][0]["ocr_text"]


def test_master_specification_has_more_than_200_pages(messy):
    for item, _, data in _of_kind(messy, "long_document"):
        assert len(PdfReader(io.BytesIO(data)).pages) >= 200, item["id"]


def test_workbook_has_several_sheets_and_a_hidden_one(messy):
    for item, _, data in _of_kind(messy, "multi_sheet"):
        workbook = load_workbook(io.BytesIO(data))
        assert len(workbook.sheetnames) >= 5, item["id"]
        assert any(sheet.sheet_state == "hidden" for sheet in workbook.worksheets), item["id"]


def test_empty_and_corrupt_files(dataset, messy):
    for item, _, data in _of_kind(messy, "empty"):
        assert data == b"", item["id"]
    for item, document, _ in _of_kind(messy, "corrupt"):
        assert dataset.text(document["document_id"]) is None, item["id"]


def test_wrong_extensions_and_legacy_encodings(dataset, messy):
    for item, document, data in _of_kind(messy, "wrong_extension"):
        assert not data.startswith((b"%PDF", b"PK")), item["id"]
        assert dataset.text(document["document_id"]), item["id"]
    for item, _, data in _of_kind(messy, "legacy_encoding"):
        with pytest.raises(UnicodeDecodeError):
            data.decode("utf-8")
        assert "Zähldatum" in data.decode("cp1252"), item["id"]


def test_duplicates_are_byte_identical_to_another_document(dataset, messy):
    hashes = Counter(d["sha256"] for d in dataset.documents().values())
    for item, document, _ in _of_kind(messy, "duplicate"):
        assert hashes[document["sha256"]] >= 2, item["id"]
