"""Shared fixtures: the generated dataset, its document registries, file text and table rows.

The tests read the committed output in the repository. Point them at another
build with ``EMPIRE_DATASET_ROOT=/path/to/output``.
"""

import csv
import json
import os
from pathlib import Path

import pytest

from generator.config import ROOT
from generator.ground_truth import TENANTS
from tests.textract import extract, normalize

DATASET = Path(os.environ.get("EMPIRE_DATASET_ROOT", ROOT)).resolve()


class Dataset:
    def __init__(self, root: Path):
        self.root = root
        self.bucket_root = root / "bucket"
        self.seed_root = root / "db" / "seed"
        self.ground_truth = root / "ground_truth"
        self._tables: dict[tuple[str, str], list[dict]] = {}
        self._texts: dict[str, str | None] = {}
        self._documents: dict[str, dict] = {}

    def json(self, name: str):
        return json.loads((self.ground_truth / name).read_text(encoding="utf-8"))

    def table(self, tenant: str, table: str) -> list[dict]:
        if (tenant, table) not in self._tables:
            with open(self.seed_root / tenant / f"{table}.csv", newline="", encoding="utf-8") as handle:
                self._tables[(tenant, table)] = list(csv.DictReader(handle))
        return self._tables[(tenant, table)]

    def documents(self) -> dict[str, dict]:
        """Every registered document of both tenants, by document_id."""
        if not self._documents:
            self._documents = {row["document_id"]: {**row, "tenant": tenant} for tenant in TENANTS for row in self.table(tenant, "documents")}
        return self._documents

    def path(self, document: dict) -> Path:
        return self.bucket_root / document["bucket"] / document["object_key"]

    def text(self, document_id: str) -> str | None:
        """The document's whitespace-normalized text, or None if it cannot be read as text."""
        if document_id not in self._texts:
            document = self.documents()[document_id]
            text = extract(self.path(document).read_bytes(), document["object_key"])
            self._texts[document_id] = None if text is None else normalize(text)
        return self._texts[document_id]

    def rows(self, tenant: str, table: str, key: dict) -> list[dict]:
        name = table.split(".", 1)[1]
        return [row for row in self.table(tenant, name) if all(row[column] == str(value) for column, value in key.items())]


@pytest.fixture(scope="session")
def dataset() -> Dataset:
    if not (DATASET / "ground_truth" / "questions.json").exists():
        pytest.fail(f"no generated dataset under {DATASET}; run `uv run python -m generator` first")
    return Dataset(DATASET)
