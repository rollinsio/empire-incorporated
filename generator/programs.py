"""Programs, work packages, milestones, tasks and budget lines."""

from dataclasses import dataclass
from datetime import date, timedelta

from generator import canon
from generator.config import AS_OF
from generator.labels import CONFIDENTIAL, INTERNAL
from generator.personnel import Personnel
from generator.rand import stream

CATEGORIES = ("Labor", "Materials", "Subcontracts", "Facilities", "Contingency")
CATEGORY_WEIGHTS = (0.31, 0.34, 0.22, 0.08, 0.05)

OTHER_PROGRAM_PACKAGES = {
    "PRG-CSL": ("HFO", ["Line 4 tooling", "Line 5 tooling", "Solar panel bonding cell", "Cabin module assembly", "Ion engine test stand", "Final acceptance flight line", "Workforce training", "Production scheduling system"]),
    "PRG-SCA": ("CCS", ["Archive rack replacement", "Data tape migration", "Tower antenna refit", "Climate control upgrade", "Archive index service", "Network switch refresh", "Records retention review"]),
    "PRG-EAD": ("AGR", ["Greenhouse hall expansion", "Seed bank cold store", "Storm-proof glazing", "Vertical farm pilot line", "Cargo landing pad resurfacing", "Laboratory instrumentation"]),
    "PRG-HQC": ("HRA", ["Floor plan consolidation", "Relocation logistics", "Badge system migration", "Records digitization", "Cafeteria refit"]),
}

TASK_VERBS = (
    "Review", "Update", "Fabricate", "Inspect", "Install", "Align", "Calibrate", "Weld", "Torque-check", "Test",
    "Document", "Re-qualify", "Survey", "Procure", "Rework", "Verify", "Integrate", "Load-test", "Commission", "Close out",
)
TASK_OBJECTS = (
    "mounting brackets", "conduit runs", "interface drawings", "cable harness", "access panels", "coolant lines",
    "seal assemblies", "sensor leads", "support struts", "control firmware", "inspection records", "bolt pattern",
    "test procedure", "shielding tiles", "hull fasteners", "maintenance hatches", "grounding straps", "spares kit",
)

STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_COMPLETE, STATUS_ON_HOLD = "NOT_STARTED", "IN_PROGRESS", "COMPLETE", "ON_HOLD"

# Program-level milestones of the station program.
STATION_MILESTONES = [
    {"milestone_id": "MS-SHV-P1", "name": "Superstructure closure", "planned_date": date(2025, 12, 19), "forecast_date": date(2026, 2, 27), "actual_date": date(2026, 3, 6), "status": "COMPLETE"},
    {"milestone_id": "MS-SHV-P2", "name": "Main reactor first power", "planned_date": date(2026, 4, 30), "forecast_date": date(2026, 5, 22), "actual_date": date(2026, 5, 22), "status": "COMPLETE"},
    {"milestone_id": "MS-SHV-P3", "name": "First resident crew move-in", "planned_date": date(2026, 11, 2), "forecast_date": date(2026, 11, 16), "actual_date": None, "status": "PLANNED"},
    {"milestone_id": "MS-SHV-P4", "name": "Shipyard first keel laying", "planned_date": date(2027, 1, 18), "forecast_date": date(2027, 1, 18), "actual_date": None, "status": "PLANNED"},
    {"milestone_id": "MS-SHV-P5", "name": "Full operational capability", "planned_date": date(2027, 6, 30), "forecast_date": date(2027, 6, 30), "actual_date": None, "status": "PLANNED"},
]


@dataclass
class WorkPackage:
    wp_id: str
    program_id: str
    wbs_code: str
    name: str
    system_code: str | None
    component_code: str | None
    owner_id: str
    department: str
    start_date: date
    end_date: date
    budget_mcr: float
    actual_mcr: float
    percent_complete: float
    status: str
    sensitivity: str


@dataclass
class Programs:
    programs: list[dict]
    work_packages: list[WorkPackage]
    milestones: list[dict]
    tasks: list[dict]
    budget_lines: list[dict]
    systems: list[dict]
    components: list[dict]

    def wps_for(self, system_code: str) -> list[WorkPackage]:
        return [wp for wp in self.work_packages if wp.system_code == system_code]


def _owner(rng, personnel: Personnel, dept: str, min_grade: int = 9) -> str:
    candidates = [e for e in personnel.active(dept) if min_grade <= e.grade <= 12]
    return rng.choice(candidates).employee_id


def _progress(rng, start: date, end: date) -> tuple[float, str]:
    if start > AS_OF:
        return 0.0, STATUS_NOT_STARTED
    planned = min(1.0, (AS_OF - start).days / max(1, (end - start).days))
    actual = round(min(1.0, planned * rng.uniform(0.72, 1.04)) * 100, 1)
    if actual >= 100:
        return 100.0, STATUS_COMPLETE
    if rng.random() < 0.04:
        return actual, STATUS_ON_HOLD
    return actual, STATUS_IN_PROGRESS


def _split(total: float, weights: list[float]) -> list[float]:
    """Split ``total`` by ``weights`` into values with two decimals that sum exactly to ``total``."""
    scale = sum(weights)
    parts = [round(total * w / scale, 2) for w in weights]
    parts[-1] = round(total - sum(parts[:-1]), 2)
    return parts


def _systems_and_components() -> tuple[list[dict], list[dict]]:
    systems, components = [], []
    for code, spec in canon.SYSTEMS.items():
        systems.append({"system_code": code, "name": spec["name"], "lead_department_id": canon.DEPT_ID[spec["dept"]], "summary": spec["summary"], "sensitivity": spec["label"]})
        for comp_code, comp_name, params in spec["components"]:
            components.append({"component_code": f"{code}-{comp_code}", "system_code": code, "name": comp_name, "parameter_count": len(params), "sensitivity": spec["label"]})
    return systems, components


def _station_packages(rng, personnel: Personnel) -> list[WorkPackage]:
    program_start = date(2020, 1, 6)
    packages: list[WorkPackage] = []
    for sys_index, (code, spec) in enumerate(canon.SYSTEMS.items()):
        entries = [("Design & analysis", None)]
        entries += [(f"Fabricate & install {name.lower()}", comp_code) for comp_code, name, _ in spec["components"]]
        entries += [("Integration & test", None)]
        for n, (name, comp_code) in enumerate(entries, start=1):
            if name == "Design & analysis":
                start = program_start + timedelta(days=rng.randint(0, 200))
                end = start + timedelta(days=rng.randint(600, 1000))
            elif name == "Integration & test":
                start = date(2025, 6, 2) + timedelta(days=rng.randint(0, 240))
                end = start + timedelta(days=rng.randint(420, 700))
            else:
                start = date(2022, 1, 3) + timedelta(days=rng.randint(0, 900))
                end = start + timedelta(days=rng.randint(360, 1100))
            end = min(end, date(2027, 6, 15))
            percent, status = _progress(rng, start, end)
            packages.append(WorkPackage(
                wp_id=f"WP-SHV-{code}-{n:02d}", program_id=canon.MAIN_PROGRAM, wbs_code=f"1.{sys_index + 1}.{n}",
                name=f"{spec['name']}: {name}", system_code=code,
                component_code=f"{code}-{comp_code}" if comp_code else None,
                owner_id=_owner(rng, personnel, spec["dept"]), department=spec["dept"],
                start_date=start, end_date=end, budget_mcr=0.0, actual_mcr=0.0,
                percent_complete=percent, status=status, sensitivity=CONFIDENTIAL,
            ))
    return packages


def _other_packages(rng, personnel: Personnel, program: tuple) -> list[WorkPackage]:
    program_id, code, _, _, start, target, _ = program
    dept, names = OTHER_PROGRAM_PACKAGES[program_id]
    packages = []
    span = (target - start).days
    for n, name in enumerate(names, start=1):
        wp_start = start + timedelta(days=int(span * rng.uniform(0, 0.5)))
        wp_end = min(target, wp_start + timedelta(days=int(span * rng.uniform(0.3, 0.6))))
        percent, status = _progress(rng, wp_start, wp_end)
        packages.append(WorkPackage(
            wp_id=f"WP-{code}-{n:02d}", program_id=program_id, wbs_code=f"{n}",
            name=name, system_code=None, component_code=None,
            owner_id=_owner(rng, personnel, dept), department=dept,
            start_date=wp_start, end_date=wp_end, budget_mcr=0.0, actual_mcr=0.0,
            percent_complete=percent, status=status, sensitivity=CONFIDENTIAL,
        ))
    return packages


def _assign_budgets(rng, packages: list[WorkPackage], total_mcr: float) -> None:
    budgets = _split(total_mcr, [rng.uniform(0.5, 3.0) for _ in packages])
    for wp, budget in zip(packages, budgets):
        wp.budget_mcr = budget
        wp.actual_mcr = round(budget * wp.percent_complete / 100 * rng.uniform(0.92, 1.18), 2)


def _milestones(rng, packages: list[WorkPackage]) -> list[dict]:
    rows = []
    names = ("Preliminary design review", "Critical design review", "Fabrication complete", "Installation complete", "Acceptance test complete")
    for wp in packages:
        chosen = names[:2] + names[-1:] if wp.component_code is None else names[2:]
        for n, name in enumerate(chosen, start=1):
            fraction = n / (len(chosen) + 0.3)
            planned = wp.start_date + timedelta(days=int((wp.end_date - wp.start_date).days * fraction))
            slip = timedelta(days=rng.choice((0, 0, 0, 7, 14, 21, 35, 60)))
            forecast = planned + slip
            actual = forecast if forecast <= AS_OF and wp.percent_complete >= fraction * 100 else None
            rows.append({
                "milestone_id": f"MS-{wp.wp_id[3:]}-{n}", "program_id": wp.program_id, "wp_id": wp.wp_id, "name": name,
                "planned_date": planned, "forecast_date": forecast, "actual_date": actual,
                "status": "COMPLETE" if actual else ("LATE" if forecast < AS_OF else "PLANNED"), "sensitivity": INTERNAL,
            })
    rows += [{"program_id": canon.MAIN_PROGRAM, "wp_id": None, "sensitivity": INTERNAL, **milestone} for milestone in STATION_MILESTONES]
    return rows


def _tasks(rng, personnel: Personnel, packages: list[WorkPackage]) -> list[dict]:
    rows = []
    counter = 0
    for wp in packages:
        team = [e for e in personnel.active(wp.department) if e.grade <= 9] + [e for e in personnel.active("QAT") if e.grade <= 6][:8]
        n_tasks = rng.randint(40, 95) if wp.program_id == canon.MAIN_PROGRAM else rng.randint(15, 40)
        span = max(1, (wp.end_date - wp.start_date).days)
        for _ in range(n_tasks):
            counter += 1
            created = wp.start_date + timedelta(days=rng.randrange(span))
            due = created + timedelta(days=rng.randint(5, 90))
            done_cutoff = wp.percent_complete / 100
            position = (created - wp.start_date).days / span
            if created > AS_OF:
                status, completed = "BACKLOG", None
            elif position < done_cutoff * 0.95 or wp.status == STATUS_COMPLETE:
                status = "DONE"
                completed = min(AS_OF, created + timedelta(days=rng.randint(2, 80)))
            else:
                status, completed = rng.choice(("OPEN", "IN_PROGRESS", "IN_PROGRESS", "BLOCKED")), None
            obj = rng.choice(TASK_OBJECTS)
            target = wp.name.split(": ", 1)[-1] if wp.component_code else wp.name
            rows.append({
                "task_id": f"TSK-{counter:06d}", "wp_id": wp.wp_id,
                "title": f"{rng.choice(TASK_VERBS)} {obj} ({target})",
                "assignee_id": rng.choice(team).employee_id,
                "status": status, "priority": rng.choice(("LOW", "MEDIUM", "MEDIUM", "HIGH", "CRITICAL")),
                "created_date": created, "due_date": due, "completed_date": completed,
                "estimate_hours": rng.choice((4, 8, 12, 16, 24, 40, 80)), "sensitivity": INTERNAL,
            })
    return rows


def _budget_lines(rng, program: tuple, packages: list[WorkPackage]) -> list[dict]:
    program_id, _, _, _, start, target, total = program
    years = list(range(start.year, target.year + 1))
    year_weights = [1 + 2.5 * (1 - abs((i - len(years) * 0.6) / len(years))) for i in range(len(years))]
    rows = []
    for year, year_total in zip(years, _split(total, year_weights)):
        for quarter, quarter_total in zip(range(1, 5), _split(year_total, [1, 1.05, 1.1, 0.95])):
            for category, planned in zip(CATEGORIES, _split(quarter_total, list(CATEGORY_WEIGHTS))):
                quarter_end = date(year, quarter * 3, 28)
                if quarter_end <= AS_OF:
                    actual = round(planned * rng.uniform(0.9, 1.12), 2)
                else:
                    actual = None
                rows.append({
                    "budget_line_id": f"BL-{program_id[4:]}-{year}-Q{quarter}-{category[:3].upper()}",
                    "program_id": program_id, "fiscal_year": year, "quarter": quarter, "category": category,
                    "planned_mcr": planned, "actual_mcr": actual,
                    "sensitivity": CONFIDENTIAL,
                })
    return rows


def build(personnel: Personnel) -> Programs:
    rng = stream("programs")
    systems, components = _systems_and_components()
    packages: list[WorkPackage] = []
    budget_lines: list[dict] = []
    programs = []
    roles = {(program, role): handle for program, handle, role, _, end in canon.PROGRAM_ROLES if end is None}
    for program in canon.PROGRAMS:
        program_id, code, name, status, start, target, total = program
        program_packages = _station_packages(rng, personnel) if program_id == canon.MAIN_PROGRAM else _other_packages(rng, personnel, program)
        _assign_budgets(rng, program_packages, total)
        packages += program_packages
        budget_lines += _budget_lines(rng, program, program_packages)
        programs.append({
            "program_id": program_id, "code": code, "name": name,
            "executive_sponsor_id": personnel.by_handle[roles[(program_id, "EXECUTIVE_SPONSOR")]].employee_id,
            "program_director_id": personnel.by_handle[roles[(program_id, "PROGRAM_DIRECTOR")]].employee_id,
            "status": status, "start_date": start, "target_completion": target,
            "budget_mcr": total, "sensitivity": CONFIDENTIAL,
        })
    return Programs(
        programs=programs,
        work_packages=packages,
        milestones=_milestones(rng, packages),
        tasks=_tasks(rng, personnel, packages),
        budget_lines=budget_lines,
        systems=systems,
        components=components,
    )

