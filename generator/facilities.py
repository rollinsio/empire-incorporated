"""Facility incidents and the document access log."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from generator.config import AS_OF
from generator.docs.model import DocumentStore
from generator.labels import INTERNAL, may_see
from generator.personnel import Personnel
from generator.rand import stream
from generator.telemetry import PEAK_AT

# (category, severity, summary template)
INCIDENT_TEMPLATES = [
    ("LOST_PROPERTY", "LOW", "Employee badge reported lost near {place}; badge deactivated and replaced."),
    ("LOST_PROPERTY", "LOW", "Datapad left in a meeting room at {place}; returned to its owner by reception."),
    ("FACILITIES", "LOW", "Coolant leak reported during shift change at {place}; drip tray fitted and seal replaced."),
    ("FACILITIES", "MEDIUM", "Water leak from a ceiling duct at {place}; area closed for two hours while the joint was resealed."),
    ("FACILITIES", "LOW", "Turbolift car stopped between levels near {place}; passengers released after twelve minutes."),
    ("FACILITIES", "LOW", "Fire alarm triggered by welding fumes at {place}; no fire, detector recalibrated."),
    ("FACILITIES", "MEDIUM", "Power flicker in a zone substation feeding {place}; backup generators carried the load."),
    ("SAFETY", "LOW", "Gravity plate fault at {place}; an employee slipped and received first aid on site."),
    ("SAFETY", "LOW", "Nutrient solution spilled at {place}; cleaned up following the spill procedure."),
    ("SAFETY", "MEDIUM", "Scaffold handrail found loose at {place}; scaffold tagged out until repaired."),
]
PLACES = (
    "Docking Bay 94 corridor", "Habitation block H-3 laundry", "Hangar 327 control room", "Scarif Archive Depot lobby",
    "Eriadu yard gate 3", "Reactor access walkway 7", "Operations centre anteroom", "Compactor 3263827 access hatch",
    "Eadu greenhouse hall 2", "Coruscant Headquarters floor 41", "Tram platform, band 6", "Research laboratory wing B",
)

# The incident that coincides with the reactor temperature peak (see generator/telemetry.py).
PEAK_INCIDENT = {
    "incident_id": "FI-2026-031",
    "opened_date": PEAK_AT.date(),
    "closed_date": PEAK_AT.date() + timedelta(days=2),
    "severity": "MEDIUM",
    "category": "FACILITIES",
    "summary": "Coolant pump trip in Zone Z11 at 14:00 station time while the reactor core temperature was elevated; pump restarted after 40 minutes, no injuries.",
    "status": "CLOSED",
    "sensitivity": INTERNAL,
}


@dataclass
class Facilities:
    incidents: list[dict]


def _incidents(rng, personnel: Personnel) -> list[dict]:
    reporters = [e for e in personnel.active("FAC") if e.grade >= 3]
    rows = [{**PEAK_INCIDENT, "reported_by": personnel.by_handle["quayle"].employee_id}]
    used = {PEAK_INCIDENT["incident_id"]}
    for _ in range(46):
        category, severity, template = rng.choice(INCIDENT_TEMPLATES)
        opened = date(2024, 1, 8) + timedelta(days=rng.randint(0, (AS_OF - date(2024, 1, 8)).days - 5))
        while True:
            incident_id = f"FI-{opened.year}-{rng.randint(1, 60):03d}"
            if incident_id not in used:
                used.add(incident_id)
                break
        closed = opened + timedelta(days=rng.randint(1, 30))
        rows.append({
            "incident_id": incident_id, "opened_date": opened, "closed_date": closed if closed < AS_OF else None,
            "severity": severity, "category": category, "summary": template.format(place=rng.choice(PLACES)),
            "status": "CLOSED" if closed < AS_OF else "OPEN", "sensitivity": INTERNAL,
            "reported_by": rng.choice(reporters).employee_id,
        })
    rows.sort(key=lambda r: (r["opened_date"], r["incident_id"]))
    return rows


def build(personnel: Personnel) -> Facilities:
    return Facilities(_incidents(stream("facilities"), personnel))


def build_access_logs(personnel: Personnel, store: DocumentStore) -> list[dict]:
    """Nine months of document opens. The result follows the reader's access level and the document's label."""
    rng = stream("access-logs")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    hours = int((datetime(2026, 9, 30, 23, 0, tzinfo=timezone.utc) - start).total_seconds() // 3600)
    readers = personnel.active()
    docs = store.docs
    rows = []
    for _ in range(42_000):
        employee = rng.choice(readers)
        doc = rng.choice(docs)
        at = start + timedelta(hours=rng.randrange(hours), minutes=rng.randrange(60), seconds=rng.randrange(60))
        allowed = may_see(employee.access_level, doc.label)
        # Most people only open what they may see; a few stray clicks are denied.
        if not allowed and rng.random() < 0.85:
            continue
        rows.append({"accessed_at": at, "employee_id": employee.employee_id, "document_id": doc.document_id,
                     "action": rng.choice(("VIEW", "VIEW", "VIEW", "DOWNLOAD", "PRINT")), "terminal_id": f"TRM-{rng.randint(1000, 9999)}",
                     "result": "ALLOWED" if allowed else "DENIED"})
    rows.sort(key=lambda r: (r["accessed_at"], r["employee_id"], r["document_id"]))
    for n, row in enumerate(rows, start=1):
        row["log_id"] = n
    return rows
