"""Extract the readable text of any file in the buckets, by content rather than by extension.

Returns ``None`` for files that cannot be read as text (images, scans without
a text layer, corrupt files), so callers can tell "empty" from "unreadable".
"""

import io
import re
import zipfile
from email import policy
from email.parser import BytesParser

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader
from pypdf.errors import PdfReadError

WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return WHITESPACE.sub(" ", text).strip()


def _decode(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def _pdf(data: bytes) -> str | None:
    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except (PdfReadError, ValueError, KeyError):
        return None


def _docx(data: bytes) -> str:
    document = Document(io.BytesIO(data))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts += [cell.text for cell in row.cells]
    for section in document.sections:
        parts += [p.text for p in section.header.paragraphs] + [p.text for p in section.footer.paragraphs]
    return "\n".join(parts)


def _xlsx(data: bytes) -> str:
    workbook = load_workbook(io.BytesIO(data), read_only=True)
    parts = []
    for sheet in workbook.worksheets:
        parts.append(sheet.title)
        for row in sheet.iter_rows(values_only=True):
            parts += [str(value) for value in row if value is not None]
    return "\n".join(parts)


def _eml(data: bytes) -> str:
    message = BytesParser(policy=policy.default).parsebytes(data)
    parts = [f"{name}: {value}" for name, value in message.items()]
    for part in message.walk():
        if part.get_content_maintype() == "text":
            parts.append(part.get_content())
    return "\n".join(parts)


def _ics(text: str) -> str:
    """Unfold content lines and unescape TEXT values (RFC 5545)."""
    unfolded = text.replace("\r\n ", "").replace("\n ", "")
    return unfolded.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def extract(data: bytes, key: str) -> str | None:
    if not data:
        return ""
    if data.startswith(b"%PDF"):
        return _pdf(data)
    if data.startswith(b"PK"):
        try:
            names = zipfile.ZipFile(io.BytesIO(data)).namelist()
            if "word/document.xml" in names:
                return _docx(data)
            if "xl/workbook.xml" in names:
                return _xlsx(data)
        except (zipfile.BadZipFile, KeyError, ValueError):
            return None
        return None
    if data.startswith((b"\x89PNG", b"\xff\xd8")):
        return None
    if key.endswith(".eml"):
        return _eml(data)
    text = _decode(data)
    if "\x00" in text or sum(not (ch.isprintable() or ch.isspace()) for ch in text[:2000]) > 20:
        return None
    return _ics(text) if key.endswith(".ics") else text
