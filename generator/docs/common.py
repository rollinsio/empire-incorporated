"""Small helpers shared by the document builders."""

import random
import re
from datetime import date

from generator.config import AS_OF
from generator.context import Context
from generator.labels import INTERNAL
from generator.programs import WorkPackage

# Weeks without a meeting (holidays), shared by the minutes and the calendar invites.
REVIEW_SKIP = (date(2025, 12, 25), date(2026, 1, 1))
ERIADU_SKIP = (date(2025, 12, 23), date(2025, 12, 30))

ENVIRONMENT_ROWS = [
    ["Operating pressure", "Vacuum to 110 kPa"],
    ["Radiation, total dose", "Station design environment, class R3"],
    ["Thermal cycling", "200 cycles, operating range"],
    ["Vibration", "Station-keeping manoeuvre profile, level 2"],
    ["Electromagnetic compatibility", "Station EMC standard, category B"],
]

GENERIC_REQUIREMENTS = [
    ("Maintainability", "Line-replaceable units shall be replaceable by a crew of four within one shift."),
    ("Safety", "Single faults shall not cause loss of the zone or injury to crew."),
    ("Workmanship", "Welds and fasteners shall meet the station workmanship standard SHV-QA-STD-0002."),
    ("Marking", "Every assembly shall carry its drawing number, revision and serial number."),
    ("Documentation", "Acceptance data packages shall be delivered with every unit."),
]


def slug(text: str) -> str:
    text = text.lower().replace("&", "and").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def credits(value: float) -> str:
    return f"{value:,.2f} credits"


def mcr(value: float) -> str:
    return f"{value:,.2f} Mcr"


def pick(rng: random.Random, weighted: dict[str, int]) -> str:
    names = sorted(weighted)
    return rng.choices(names, weights=[weighted[n] for n in names], k=1)[0]


def de_date(day: date) -> str:
    return day.strftime("%d.%m.%Y")


def leader_row(ctx: Context, entity_type: str, entity_id: str, role: str, on: date) -> dict:
    """The leadership row in force on ``on``."""
    return next(row for row in ctx.personnel.leadership
                if (row["entity_type"], row["entity_id"], row["role"]) == (entity_type, entity_id, role)
                and row["start_date"] <= on <= (row["end_date"] or AS_OF))


def leadership_source(ctx: Context, row: dict) -> dict:
    return ctx.truth.row_source("leadership", INTERNAL, leadership_id=row["leadership_id"])


def progress_on(wp: WorkPackage, on: date) -> float:
    """Work-package progress on a past day, interpolated between its start and today's value."""
    if on <= wp.start_date:
        return 0.0
    if wp.status == "COMPLETE" and on >= wp.end_date:
        return 100.0
    elapsed = (min(on, AS_OF) - wp.start_date).days / max(1, (AS_OF - wp.start_date).days)
    return round(wp.percent_complete * min(1.0, elapsed), 1)
