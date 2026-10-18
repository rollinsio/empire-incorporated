"""Everything a Kuat Drive Yards document builder needs."""

import random
from dataclasses import dataclass
from pathlib import Path

from generator.config import KDY_BUCKET, KDY_DATABASE
from generator.docs.model import DocumentStore
from generator.kdy import data, world
from generator.rand import stream
from generator.supply import Supply
from generator.truth import Collector, Recorder


@dataclass
class KdyContext:
    data: data.KdyData
    store: DocumentStore
    truth: Recorder

    def rng(self, name: str) -> random.Random:
        return stream(f"kdy:docs:{name}")

    def name(self, employee_id: str | None) -> str | None:
        return self.data.employee(employee_id).name if employee_id else None


def make_context(bucket_root: Path, collector: Collector, empire_supply: Supply, taken_names: set[tuple[str, str]]) -> KdyContext:
    store = DocumentStore(root=bucket_root / KDY_BUCKET, bucket=KDY_BUCKET, company=world.COMPANY, id_prefix="KDY-DOC")
    return KdyContext(
        data=data.build(empire_supply, taken_names),
        store=store,
        truth=Recorder(collector=collector, store=store, tenant="kdy", database=KDY_DATABASE),
    )
