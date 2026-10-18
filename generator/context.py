"""Everything an Empire Incorporated document builder needs.

Builders call ``ctx.store.add(Doc(...))`` to write a file and use
``ctx.truth`` (see ``generator.truth``) to plant test cases and offer
ground-truth questions.
"""

import random
from dataclasses import dataclass
from datetime import date

from generator.docs.model import DocumentStore
from generator.engineering import Engineering
from generator.facilities import Facilities
from generator.hr import HrRecords
from generator.personnel import Employee, Personnel
from generator.programs import Programs
from generator.rand import stream
from generator.supply import Supply
from generator.telemetry import Telemetry
from generator.truth import Recorder


@dataclass
class Context:
    personnel: Personnel
    hr: HrRecords
    programs: Programs
    supply: Supply
    telemetry: Telemetry
    facilities: Facilities
    engineering: Engineering
    store: DocumentStore
    truth: Recorder

    def rng(self, name: str) -> random.Random:
        return stream(f"docs:{name}")

    def employee(self, employee_id: str) -> Employee:
        return self.personnel.by_id[employee_id]

    def name(self, employee_id: str | None) -> str | None:
        return self.personnel.by_id[employee_id].name if employee_id else None

    def person(self, handle: str) -> Employee:
        return self.personnel.by_handle[handle]

    def head_of(self, department: str, on: date) -> Employee:
        return self.personnel.head_of(department, on) or self.personnel.by_handle["tarrow"]
