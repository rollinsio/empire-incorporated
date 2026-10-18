"""The document model shared by every builder, and the store that writes files and records them.

Rich documents (Markdown, PDF, DOCX) are described as a list of blocks, so one
builder can emit any of the three formats:

    ("h1" | "h2" | "h3", text)
    ("p", text)
    ("bullets" | "numbered", [text, ...])
    ("table", [header, ...], [[cell, ...], ...])
    ("kv", [(key, value), ...])
    ("note", text)                 a boxed call-out
    ("hidden", text)               text a reader would not see (injection tests)
    ("pagebreak",)
"""

import hashlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from generator.labels import LABELS

Block = tuple

APPROVED, DRAFT, IN_REVIEW, SUPERSEDED, REJECTED = "APPROVED", "DRAFT", "IN_REVIEW", "SUPERSEDED", "REJECTED"
APPROVAL_STATUSES = (APPROVED, DRAFT, IN_REVIEW, SUPERSEDED, REJECTED)


@dataclass
class Sheet:
    """One worksheet of an XLSX document."""

    name: str
    rows: list[list]
    hidden: bool = False
    merges: tuple[str, ...] = ()
    column_widths: tuple[int, ...] = ()


@dataclass
class ScannedPages:
    """Image-only PDF content: one JPEG per page and no text layer."""

    pages: list[bytes]


@dataclass
class Doc:
    doc_number: str
    title: str
    doc_type: str
    fmt: str
    key: str
    label: str
    created_date: date
    content: object
    true_sensitivity: str | None = None
    revision: str = "1"
    approval_status: str = APPROVED
    system_code: str | None = None
    program_id: str | None = None
    author_id: str | None = None
    author_name: str | None = None
    approver_id: str | None = None
    approver_name: str | None = None
    approved_date: date | None = None
    language: str = "en"
    supersedes_key: str | None = None
    tags: tuple[str, ...] = ()
    notes: str | None = None
    # Filled in by the store.
    company: str = ""
    document_id: str = ""
    size_bytes: int = 0
    sha256: str = ""

    def __post_init__(self):
        if self.true_sensitivity is None:
            self.true_sensitivity = self.label
        assert self.label in LABELS and self.true_sensitivity in LABELS, self.doc_number
        assert self.approval_status in APPROVAL_STATUSES, self.approval_status


@dataclass
class DocumentStore:
    """Writes each document under ``root`` and keeps the registry row for it."""

    root: Path
    bucket: str
    company: str
    id_prefix: str = "DOC"
    docs: list[Doc] = field(default_factory=list)
    _keys: set[str] = field(default_factory=set)

    def add(self, doc: Doc) -> Doc:
        from generator.docs.render import render

        if doc.key in self._keys:
            raise ValueError(f"duplicate storage key: {doc.key}")
        self._keys.add(doc.key)
        doc.company = self.company
        data = render(doc)
        path = self.root / doc.key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        doc.document_id = f"{self.id_prefix}-{len(self.docs) + 1:05d}"
        doc.size_bytes = len(data)
        doc.sha256 = hashlib.sha256(data).hexdigest()
        doc.content = None  # release memory; the file on disk is the record
        self.docs.append(doc)
        return doc

    def by_key(self, key: str) -> Doc:
        return next(d for d in self.docs if d.key == key)

    def by_number(self, doc_number: str) -> list[Doc]:
        return [d for d in self.docs if d.doc_number == doc_number]

    def uri(self, doc: Doc) -> str:
        return f"s3://{self.bucket}/{doc.key}"
