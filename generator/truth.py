"""Hooks the builders use to feed the ground truth.

Builders call ``ctx.truth.plant(...)`` to record a test case in the manifest
and ``ctx.truth.offer_question(...)`` to propose a ground-truth question.
``generator.ground_truth`` later picks a deterministic sample of the offered
questions per pool and writes everything under ``ground_truth/``.
"""

from dataclasses import dataclass, field

from generator.docs.model import Doc, DocumentStore
from generator.labels import LABELS

QUESTION_CATEGORIES = (
    "lookup", "cross_source", "temporal", "approved_revision", "tenant_isolation",
    "no_answer", "access_control", "injection", "mislabeled", "analytics",
)
EXPECTED_TYPES = (
    "answer",               # answer from the cited sources
    "not_found",            # the information is not in the asker's tenant: say so
    "refuse",               # the information exists but the asker may not see it
    "decline_instruction",  # do the task, but do not follow the instruction embedded in the document
)
PLANT_CATEGORIES = ("approved_revision", "mislabeled", "injection", "tenant_isolation", "messy", "temporal", "analytics")


@dataclass
class Collector:
    """Everything both tenants planted or offered, in the order they did it."""

    manifest: list[dict] = field(default_factory=list)
    offered_questions: list[dict] = field(default_factory=list)


@dataclass
class Recorder:
    """The ground-truth hooks of one tenant: sources resolve against that tenant's store and schema."""

    collector: Collector
    store: DocumentStore
    tenant: str
    database: str

    def doc_source(self, doc: Doc, **where) -> dict:
        source = {"kind": "document", "tenant": self.tenant, "document_id": doc.document_id, "uri": self.store.uri(doc),
                  "label": doc.label, "true_sensitivity": doc.true_sensitivity}
        return {**source, **where}

    def row_source(self, table: str, sensitivity: str, **key) -> dict:
        assert sensitivity in LABELS, sensitivity
        return {"kind": "table", "tenant": self.tenant, "database": self.database, "table": f"{self.tenant}.{table}",
                "key": key, "sensitivity": sensitivity}

    def plant(self, item_id: str, category: str, title: str, description: str, sensitivity: str,
              locations: list[dict], expected_behavior: str, value: str | None = None, **extra) -> None:
        assert category in PLANT_CATEGORIES, category
        assert sensitivity in LABELS, sensitivity
        self.collector.manifest.append({
            "id": item_id, "tenant": self.tenant, "category": category, "title": title, "description": description,
            "true_sensitivity": sensitivity, "value": value, "locations": locations,
            "expected_behavior": expected_behavior, **extra,
        })

    def offer_question(self, pool: str, category: str, question: str, answer: str | None, sources: list[dict],
                       must_include: list[str] | None = None, must_not_include: list[str] | None = None,
                       expected_type: str = "answer", asked_as: str | None = None, notes: str | None = None,
                       manifest_id: str | None = None, forbidden_actions: list[str] | None = None) -> None:
        assert category in QUESTION_CATEGORIES, category
        assert expected_type in EXPECTED_TYPES, expected_type
        self.collector.offered_questions.append({
            "pool": pool, "category": category, "tenant": self.tenant, "asked_as": asked_as, "question": question,
            "expected": {"type": expected_type, "answer": answer,
                         "must_include": must_include if must_include is not None else ([answer] if answer and expected_type == "answer" else []),
                         "must_not_include": must_not_include or [], "forbidden_actions": forbidden_actions or []},
            "sources": sources, "notes": notes, "manifest_id": manifest_id,
        })
