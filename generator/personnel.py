"""Employees, the reporting structure, employment history and leadership over time."""

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

from generator import canon
from generator.config import AS_OF, EMPIRE_DOMAIN, EMPIRE_FORMER_EMPLOYEES, EMPIRE_HEADCOUNT
from generator.labels import CONFIDENTIAL, INTERNAL, RESTRICTED
from generator.names import (
    DISTRICTS,
    FIRST_NAMES,
    GERMAN_FIRST_NAMES,
    GERMAN_HOMEWORLDS,
    GERMAN_LAST_NAMES,
    HOMEWORLDS,
    LAST_NAMES,
    RELATIONS,
    SPECIES,
    STREETS,
    email_local_part,
)
from generator.rand import stream

ACTIVE = "ACTIVE"
DEPARTED = "DEPARTED"

HQ_LOCATION = canon.HQ
STATION_LOCATION = f"{canon.STATION} (on site)"
ERIADU_LOCATION = canon.GERMAN_SITE
EADU_LOCATION = "Eadu Research Campus"
SCARIF_LOCATION = "Scarif Archive Depot"

SALARY_BANDS = {
    1: (26_000, 32_000), 2: (31_000, 38_000), 3: (37_000, 45_000), 4: (44_000, 55_000),
    5: (54_000, 66_000), 6: (64_000, 78_000), 7: (76_000, 92_000), 8: (90_000, 110_000),
    9: (108_000, 132_000), 10: (128_000, 158_000), 11: (150_000, 185_000), 12: (180_000, 230_000),
    13: (240_000, 320_000), 14: (400_000, 520_000), 15: (900_000, 1_200_000),
}

TITLES = {
    "OCH": (["Executive Clerk", "Office Coordinator"], ["Executive Assistant", "Communications Officer"], ["Senior Executive Assistant", "Policy Advisor"], ["Principal Policy Advisor"], ["Head of Executive Office"]),
    "PMO": (["Project Coordinator", "Document Controller"], ["Scheduler", "Project Analyst"], ["Project Manager", "Senior Scheduler", "Risk Manager"], ["Principal Program Manager"], ["Program Manager", "Integration Manager"]),
    "SCI": (["Laboratory Technician", "Research Assistant"], ["Research Scientist", "Data Analyst"], ["Senior Research Scientist", "Senior Data Analyst"], ["Principal Research Scientist"], ["Research Manager, Materials Science", "Research Manager, Astronomy"]),
    "AGR": (["Grow Technician", "Kitchen Technician"], ["Plant Scientist", "Food Systems Engineer"], ["Senior Plant Scientist", "Senior Food Systems Engineer"], ["Principal Plant Scientist"], ["Research Manager, Hydroponics", "Food Production Manager"]),
    "STR": (["Structural Technician", "Welding Technician"], ["Structural Engineer", "Frame Inspector"], ["Senior Structural Engineer", "Senior Frame Inspector"], ["Principal Structural Engineer"], ["Engineering Manager, Superstructure", "Engineering Manager, Internal Transit"]),
    "RPS": (["Reactor Technician", "Power Systems Technician"], ["Reactor Engineer", "Power Systems Engineer"], ["Senior Reactor Engineer", "Senior Power Systems Engineer", "Senior Thermal Engineer"], ["Principal Reactor Engineer"], ["Engineering Manager, Reactor Core", "Engineering Manager, Power Distribution", "Engineering Manager, Thermal Systems"]),
    "PRO": (["Propulsion Technician"], ["Propulsion Engineer", "Navigation Systems Engineer"], ["Senior Propulsion Engineer"], ["Principal Propulsion Engineer"], ["Engineering Manager, Station-Keeping", "Engineering Manager, Navigation"]),
    "SYD": (["Shipwright", "Crane Operator"], ["Shipyard Engineer", "Outfitting Planner"], ["Senior Shipyard Engineer", "Senior Outfitting Planner"], ["Principal Shipyard Engineer"], ["Slipway Manager", "Outfitting Manager", "Dry Dock Manager"]),
    "HFO": (["Hangar Technician", "Deck Coordinator"], ["Flight Controller", "Shuttle Pilot"], ["Senior Flight Controller", "Senior Shuttle Pilot"], ["Principal Flight Operations Officer"], ["Hangar Operations Manager", "Flight Control Manager"]),
    "LSH": (["Life Support Technician", "Habitation Technician"], ["Life Support Engineer", "Habitation Planner"], ["Senior Life Support Engineer"], ["Principal Life Support Engineer"], ["Engineering Manager, Atmospherics", "Habitation Manager"]),
    "CCS": (["Records Clerk", "Network Technician"], ["Systems Engineer", "Network Engineer"], ["Senior Systems Engineer", "Senior Network Engineer"], ["Principal Systems Architect"], ["Engineering Manager, Computer Core", "Engineering Manager, Communications"]),
    "QAT": (["Quality Inspector", "Test Technician"], ["Test Engineer", "Quality Engineer"], ["Senior Test Engineer", "Senior Quality Engineer"], ["Principal Test Engineer"], ["Test Manager", "Quality Manager"]),
    "CON": (["Construction Technician", "Welder"], ["Construction Supervisor", "Site Engineer"], ["Senior Site Engineer", "Crew Lead"], ["Principal Construction Engineer"], ["Construction Manager", "Zone Manager"]),
    "SCM": (["Procurement Clerk", "Logistics Clerk"], ["Buyer", "Logistics Analyst"], ["Senior Buyer", "Category Manager"], ["Principal Category Manager"], ["Procurement Manager", "Logistics Manager"]),
    "FIN": (["Accounts Clerk"], ["Financial Analyst", "Accountant"], ["Senior Financial Analyst", "Senior Accountant"], ["Principal Financial Analyst"], ["Controller", "Finance Manager"]),
    "HRA": (["Personnel Clerk"], ["Personnel Specialist", "Recruiter"], ["Senior Personnel Specialist", "Personnel Business Partner"], ["Principal Personnel Business Partner"], ["Personnel Manager"]),
    "LEG": (["Legal Clerk"], ["Paralegal", "Contracts Specialist"], ["Counsel", "Senior Contracts Specialist"], ["Senior Counsel"], ["Deputy General Counsel"]),
    "FAC": (["Facilities Technician", "Reception Coordinator"], ["Facilities Coordinator", "Safety Officer"], ["Senior Safety Officer", "Facilities Planner"], ["Principal Safety Engineer"], ["Facilities Manager", "Workplace Safety Manager"]),
}

GERMAN_TITLES = {
    "Construction Technician": "Bautechniker/in",
    "Welder": "Schweißer/in",
    "Construction Supervisor": "Bauaufsicht",
    "Site Engineer": "Bauingenieur/in",
    "Senior Site Engineer": "Leitende/r Bauingenieur/in",
    "Crew Lead": "Kolonnenführer/in",
    "Principal Construction Engineer": "Oberbauingenieur/in",
    "Construction Manager": "Bauleiter/in",
    "Zone Manager": "Zonenleiter/in",
    "Quality Inspector": "Qualitätsprüfer/in",
    "Test Technician": "Prüftechniker/in",
    "Test Engineer": "Prüfingenieur/in",
    "Quality Engineer": "Qualitätsingenieur/in",
    "Senior Test Engineer": "Leitende/r Prüfingenieur/in",
    "Senior Quality Engineer": "Leitende/r Qualitätsingenieur/in",
}

DEPARTURE_REASONS = (
    ("Resigned", 40), ("Retired", 14), ("Moved to a partner company", 12),
    ("Contract ended", 10), ("Relocated with family", 6),
)


def history_id(employee_id: str, index: int) -> str:
    """Id of the ``index``-th (1-based) employment history row of an employee."""
    return f"EH-{employee_id[4:]}-{index:02d}"


@dataclass
class Stint:
    """One row of employment history: the state that began on ``start``."""

    start: date
    event: str
    department: str
    title: str
    grade: int
    manager_id: str | None
    salary: int
    note: str | None = None


@dataclass
class Employee:
    employee_id: str
    badge_number: str
    first_name: str
    last_name: str
    email: str
    species: str
    homeworld: str
    department: str
    title: str
    grade: int
    access_level: str
    hire_date: date
    salary: int
    work_location: str
    language: str
    status: str = ACTIVE
    termination_date: date | None = None
    termination_reason: str | None = None
    manager_id: str | None = None
    handle: str | None = None
    comm_extension: str = ""
    home_address: str = ""
    personal_comlink: str = ""
    emergency_contact: str = ""
    history: list[Stint] = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        return self.status == ACTIVE


@dataclass
class Personnel:
    employees: list[Employee]
    by_id: dict[str, Employee]
    by_handle: dict[str, Employee]
    leadership: list[dict]
    logins: list[dict]

    def active(self, department: str | None = None) -> list[Employee]:
        return [e for e in self.employees if e.is_active and (department is None or e.department == department)]

    def head_of(self, department: str, on: date) -> Employee | None:
        for row in self.leadership:
            if row["entity_type"] == "DEPARTMENT" and row["entity_id"] == canon.DEPT_ID[department] and row["role"] == "HEAD":
                end = row["end_date"] or AS_OF
                if row["start_date"] <= on <= end:
                    return self.by_id[row["employee_id"]]
        return None

    def german_speakers(self) -> list[Employee]:
        return [e for e in self.employees if e.is_active and e.language == "de"]


def _weighted(rng, pairs):
    names, weights = zip(*pairs)
    return rng.choices(names, weights=weights, k=1)[0]


def _salary(rng, grade: int) -> int:
    low, high = SALARY_BANDS[grade]
    return int(round(rng.uniform(low, high), -2))


def _band(grade: int) -> int:
    if grade <= 3:
        return 0
    if grade <= 5:
        return 1
    if grade <= 8:
        return 2
    if grade == 9:
        return 3
    return 4


def title_for(department: str, grade: int, pick: int) -> str:
    if grade >= 13:
        return f"Director, {canon.DEPT_NAME[department]}"
    if grade == 12:
        return f"Deputy Director, {canon.DEPT_NAME[department]}"
    options = TITLES[department][_band(grade)]
    return options[pick % len(options)]


def _access_level(rng, department: str, grade: int) -> str:
    """Restricted (personal data) for directors, deputies and personnel staff; Confidential for managers and business roles."""
    if grade >= 12 or department == "OCH":
        return RESTRICTED
    if department == "HRA":
        return RESTRICTED if grade >= 4 else CONFIDENTIAL
    if grade >= 10:
        return CONFIDENTIAL
    if department in ("FIN", "LEG", "SCM", "PMO"):
        return CONFIDENTIAL if grade >= 4 else INTERNAL
    if grade >= 7:
        return CONFIDENTIAL if rng.random() < 0.5 else INTERNAL
    return INTERNAL


def _grade_for_ic(rng) -> int:
    return _weighted(rng, [(1, 10), (2, 13), (3, 12), (4, 16), (5, 14), (6, 11), (7, 9), (8, 7), (9, 8)])


def _hire_date(rng, grade: int) -> date:
    years = {0: (0.2, 6), 1: (1, 10), 2: (3, 14), 3: (5, 16), 4: (6, 18)}[_band(grade)]
    if grade >= 12:
        years = (8, 18)
    days = int(rng.uniform(*years) * 365.25)
    hired = AS_OF - timedelta(days=days)
    return max(hired, date(2008, 1, 7))


def _badge_number(rng, used: set[str]) -> str:
    # In-universe format, deliberately unlike any real-world identifier: EIB-<letter><2 digits>-<5 digits>
    while True:
        number = f"EIB-{rng.choice('ABCDEFGHJKLMNPRSTVWXZ')}{rng.randint(10, 99)}-{rng.randint(10000, 99999)}"
        if number not in used:
            used.add(number)
            return number


class _Factory:
    def __init__(self):
        self.rng = stream("personnel")
        self.used_names: set[tuple[str, str]] = set()
        self.used_badge_numbers: set[str] = set()
        self.used_extensions: set[str] = set()
        self.employees: list[Employee] = []

    def next_id(self) -> str:
        return f"EMP-{len(self.employees) + 1:05d}"

    def extension(self) -> str:
        while True:
            ext = f"x{self.rng.randint(2000, 8999)}"
            if ext not in self.used_extensions:
                self.used_extensions.add(ext)
                return ext

    def name(self, german: bool) -> tuple[str, str]:
        firsts, lasts = (GERMAN_FIRST_NAMES, GERMAN_LAST_NAMES) if german else (FIRST_NAMES, LAST_NAMES)
        while True:
            pair = (self.rng.choice(firsts), self.rng.choice(lasts))
            if pair not in self.used_names:
                self.used_names.add(pair)
                return pair

    def personal_details(self, homeworld: str) -> dict[str, str]:
        rng = self.rng
        contact_first = rng.choice(GERMAN_FIRST_NAMES if homeworld == "Eriadu" and rng.random() < 0.5 else FIRST_NAMES)
        return {
            "home_address": f"{rng.randint(1, 480)} {rng.choice(STREETS)}, {rng.choice(DISTRICTS)}, {homeworld}",
            # In-universe comlink format, unlike any real telephone number: PCL-<4 digits>-<4 digits>
            "personal_comlink": f"PCL-{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}",
            "emergency_contact": f"{contact_first} ({rng.choice(RELATIONS)})",
        }

    def add(self, **fields) -> Employee:
        first, last = fields.pop("first_name"), fields.pop("last_name")
        self.used_names.add((first, last))
        employee = Employee(
            employee_id=self.next_id(),
            badge_number=_badge_number(self.rng, self.used_badge_numbers),
            first_name=first,
            last_name=last,
            email=f"{email_local_part(first, last)}@{EMPIRE_DOMAIN}",
            comm_extension=self.extension(),
            **self.personal_details(fields["homeworld"]),
            **fields,
        )
        self.employees.append(employee)
        return employee


def _key_people(factory: _Factory) -> dict[str, Employee]:
    by_handle = {}
    for handle, (first, last, dept, title, grade, access_level, hired, species, homeworld, departed) in canon.KEY_PEOPLE.items():
        german = handle == "brandt"
        location = ERIADU_LOCATION if german else (STATION_LOCATION if dept in ("PMO", "SYD", "HFO") and grade < 14 else HQ_LOCATION)
        if handle in ("ferrante", "corvesh"):
            location = EADU_LOCATION
        employee = factory.add(
            first_name=first,
            last_name=last,
            species=species,
            homeworld=homeworld,
            department=dept,
            title=title,
            grade=grade,
            access_level=access_level,
            hire_date=hired,
            salary=_salary(factory.rng, grade),
            work_location=location,
            language="de" if german else "en",
            handle=handle,
        )
        if departed:
            employee.status = DEPARTED
            employee.termination_date = departed
            employee.termination_reason = canon.DEPARTURE_REASONS[handle]
        by_handle[handle] = employee
    return by_handle


def _generate_department(factory: _Factory, dept: str, count: int, head: Employee, key_members: list[Employee]) -> list[Employee]:
    rng = factory.rng
    generated: list[Employee] = []
    needed = count - len(key_members)
    n_deputy = 1 if count >= 40 else 0
    n_managers = max(1, math.ceil(count / 10)) if count > 12 else 1
    for index in range(needed):
        if index < n_deputy:
            grade = 12
        elif index < n_deputy + n_managers:
            grade = rng.choice((10, 10, 11))
        else:
            grade = _grade_for_ic(rng)
        german = (dept == "CON" and rng.random() < 0.62) or (dept == "QAT" and rng.random() < 0.18)
        first, last = factory.name(german)
        if german:
            location = ERIADU_LOCATION
            homeworld = _weighted(rng, GERMAN_HOMEWORLDS)
        else:
            location = rng.choice((HQ_LOCATION, STATION_LOCATION, STATION_LOCATION)) if dept in canon.ENGINEERING_DEPTS else HQ_LOCATION
            if dept == "AGR" and rng.random() < 0.5:
                location = EADU_LOCATION
            if dept == "CCS" and rng.random() < 0.15:
                location = SCARIF_LOCATION
            homeworld = _weighted(rng, HOMEWORLDS)
        title = title_for(dept, grade, rng.randrange(6))
        if german and title in GERMAN_TITLES:
            title = GERMAN_TITLES[title]
        employee = factory.add(
            first_name=first,
            last_name=last,
            species="Human" if german else _weighted(rng, SPECIES),
            homeworld=homeworld,
            department=dept,
            title=title,
            grade=grade,
            access_level=_access_level(rng, dept, grade),
            hire_date=_hire_date(rng, grade),
            salary=_salary(rng, grade),
            work_location=location,
            language="de" if german else "en",
        )
        generated.append(employee)
    # Reporting lines: deputy -> head, managers -> deputy (or head), everyone else -> a manager.
    deputies = [e for e in generated if e.grade == 12]
    managers = [e for e in generated if e.grade in (10, 11)]
    for deputy in deputies:
        deputy.manager_id = head.employee_id
    for manager in managers:
        manager.manager_id = (deputies[0] if deputies else head).employee_id
    ics = [e for e in generated if e.grade <= 9]
    leads = managers or deputies or [head]
    for index, employee in enumerate(ics):
        employee.manager_id = leads[index % len(leads)].employee_id
    return generated


def _former_employees(factory: _Factory, count: int, heads: dict[str, Employee]) -> None:
    rng = factory.rng
    depts = [code for _, code, _, _ in canon.DEPARTMENTS if code != "OCH"]
    for _ in range(count):
        dept = rng.choice(depts)
        grade = _grade_for_ic(rng)
        german = dept == "CON" and rng.random() < 0.5
        first, last = factory.name(german)
        hired = _hire_date(rng, grade)
        span = (AS_OF - hired).days
        left = hired + timedelta(days=int(span * rng.uniform(0.35, 0.97)))
        employee = factory.add(
            first_name=first,
            last_name=last,
            species=_weighted(rng, SPECIES),
            homeworld=_weighted(rng, GERMAN_HOMEWORLDS if german else HOMEWORLDS),
            department=dept,
            title=title_for(dept, grade, rng.randrange(6)),
            grade=grade,
            access_level=_access_level(rng, dept, grade),
            hire_date=hired,
            salary=_salary(rng, grade),
            work_location=ERIADU_LOCATION if german else HQ_LOCATION,
            language="de" if german else "en",
            status=DEPARTED,
            termination_date=left,
            termination_reason=_weighted(rng, DEPARTURE_REASONS),
        )
        employee.manager_id = heads[dept].employee_id


# --------------------------------------------------------------------------
# History
# --------------------------------------------------------------------------

def _between(rng, start: date, end: date) -> date:
    if end <= start:
        return start
    return start + timedelta(days=rng.randrange((end - start).days + 1))


def _generic_history(rng, employee: Employee, head_on) -> list[Stint]:
    end = employee.termination_date or AS_OF
    tenure_years = (end - employee.hire_date).days / 365.25
    promotions = 0
    if tenure_years > 1.5:
        promotions = min(employee.grade - 1, rng.randint(0, min(3, int(tenure_years // 2.5))))
    transfer = tenure_years > 3 and rng.random() < 0.14 and employee.department not in ("OCH",)
    events = sorted(_between(rng, employee.hire_date + timedelta(days=180), end - timedelta(days=30)) for _ in range(promotions + int(transfer)))
    kinds = ["PROMOTION"] * promotions + (["TRANSFER"] if transfer else [])
    rng.shuffle(kinds)
    pool = canon.ENGINEERING_DEPTS if employee.department in canon.ENGINEERING_DEPTS else ("PMO", "SCM", "FIN", "HRA", "LEG", "FAC")
    earlier_dept = rng.choice([d for d in pool if d != employee.department]) if transfer else employee.department
    # Walk backwards from the current state.
    states = []
    grade, dept, salary = employee.grade, employee.department, employee.salary
    title = employee.title
    for when, kind in reversed(list(zip(events, kinds))):
        states.append((when, kind, dept, title, grade, salary))
        if kind == "PROMOTION":
            grade -= 1
            salary = _salary(rng, grade)
        else:
            dept = earlier_dept
        title = title_for(dept, grade, rng.randrange(6))
        if employee.language == "de" and title in GERMAN_TITLES:
            title = GERMAN_TITLES[title]
    states.append((employee.hire_date, "HIRE", dept, title, grade, salary))
    history = []
    for when, kind, dept_then, title_then, grade_then, salary_then in reversed(states):
        if dept_then == employee.department:
            manager = employee.manager_id
        else:
            head = head_on(dept_then, when)
            manager = head.employee_id if head else None
        history.append(Stint(when, kind, dept_then, title_then, grade_then, manager, salary_then))
    if employee.status == DEPARTED:
        last = history[-1]
        history.append(Stint(employee.termination_date, "DEPARTURE", last.department, last.title, last.grade, last.manager_id, last.salary, employee.termination_reason))
    return history


def _key_history(rng, people: dict[str, Employee]) -> None:
    """Hand-built histories for the people the temporal ground-truth questions are about."""

    def stint(handle, when, event, dept, title, grade, manager=None, note=None):
        person = people[handle]
        salary = person.salary if (grade == person.grade and dept == person.department) else _salary(rng, grade)
        return Stint(when, event, dept, title, grade, manager, salary, note)

    tarrow, ashworth = people["tarrow"].employee_id, people["ashworth"].employee_id
    head_start = {handle: start for _, handle, start, _ in canon.DEPARTMENT_HEADS}
    for handle, person in people.items():
        dept = person.department
        if handle in ("ashworth", "quillon"):
            person.history = [stint(handle, person.hire_date, "HIRE", dept, person.title, person.grade, person.manager_id)]
            continue
        if handle == "voss":
            person.history = [
                stint(handle, person.hire_date, "HIRE", "RPS", "Principal Reactor Engineer", 9, None),
                stint(handle, date(2014, 9, 1), "PROMOTION", "RPS", "Engineering Manager, Reactor Core", 11, None),
                stint(handle, date(2018, 4, 2), "PROMOTION", "RPS", "Director, Reactor & Power Systems", 13, tarrow),
                stint(handle, date(2026, 2, 1), "TRANSFER", "PMO", person.title, person.grade, tarrow, "Moved to the PMO; succeeded at RPS by Mira Kestrel"),
            ]
            continue
        if handle == "kestrel":
            person.history = [
                stint(handle, person.hire_date, "HIRE", "RPS", "Senior Thermal Engineer", 8, None),
                stint(handle, date(2019, 3, 4), "PROMOTION", "RPS", "Engineering Manager, Thermal Systems", 10, None),
                stint(handle, date(2022, 7, 11), "PROMOTION", "RPS", "Deputy Director, Reactor & Power Systems", 12, people["voss"].employee_id),
                stint(handle, date(2026, 2, 1), "PROMOTION", "RPS", person.title, person.grade, tarrow, "Succeeded Aldric Voss as head of RPS"),
            ]
            continue
        if handle == "tolle":
            person.history = [
                stint(handle, person.hire_date, "HIRE", "STR", "Senior Structural Engineer", 8, None),
                stint(handle, date(2020, 5, 18), "PROMOTION", "STR", "Engineering Manager, Superstructure", 10, None),
                stint(handle, date(2023, 1, 9), "PROMOTION", "STR", "Deputy Director, Structural Engineering", 12, people["doyle"].employee_id),
                stint(handle, date(2025, 11, 15), "PROMOTION", "STR", person.title, person.grade, tarrow, "Succeeded Hesker Doyle as head of Structural Engineering"),
            ]
            continue
        if handle == "corvesh":
            person.history = [
                stint(handle, person.hire_date, "HIRE", "AGR", "Senior Plant Scientist", 8, None),
                stint(handle, date(2021, 2, 1), "PROMOTION", "AGR", "Research Manager, Hydroponics", 11, people["ferrante"].employee_id),
                stint(handle, date(2026, 6, 15), "PROMOTION", "AGR", person.title, person.grade, people["merriweather"].employee_id, "Interim head of Agriculture & Food Systems after the retirement of Rosalind Ferrante"),
            ]
            continue
        if handle == "tarrow":
            person.history = [
                stint(handle, person.hire_date, "HIRE", "PMO", "Deputy Program Executive", 12, ashworth),
                stint(handle, date(2012, 1, 9), "PROMOTION", "PMO", "Senior Program Executive", 13, ashworth),
                stint(handle, date(2019, 6, 3), "PROMOTION", "PMO", person.title, person.grade, ashworth),
            ]
            continue
        appointed = head_start.get(handle)
        lower_grade = max(person.grade - 2, 8)
        first_title = title_for(dept, lower_grade, 0)
        history = [stint(handle, person.hire_date, "HIRE", dept, first_title, lower_grade, None)]
        if appointed and appointed > person.hire_date:
            history.append(stint(handle, appointed, "PROMOTION", dept, person.title, person.grade, person.manager_id))
        else:
            midpoint = person.hire_date + ((person.termination_date or AS_OF) - person.hire_date) / 2
            history.append(stint(handle, midpoint, "PROMOTION", dept, person.title, person.grade, person.manager_id))
        if person.status == DEPARTED:
            history.append(stint(handle, person.termination_date, "DEPARTURE", dept, person.title, person.grade, person.manager_id, person.termination_reason))
        person.history = history


def _leadership(people: dict[str, Employee]) -> list[dict]:
    rows = []
    for dept, handle, start, end in canon.DEPARTMENT_HEADS:
        rows.append({"entity_type": "DEPARTMENT", "entity_id": canon.DEPT_ID[dept], "role": "HEAD", "employee_id": people[handle].employee_id, "start_date": start, "end_date": end})
    for program, handle, role, start, end in canon.PROGRAM_ROLES:
        rows.append({"entity_type": "PROGRAM", "entity_id": program, "role": role, "employee_id": people[handle].employee_id, "start_date": start, "end_date": end})
    return [{"leadership_id": f"LD-{n:03d}", **row} for n, row in enumerate(rows, start=1)]


def _logins(employees: list[Employee]) -> list[dict]:
    logins = []
    for username, access_level, rule in canon.LOGINS:
        employee = None
        if rule is not None:
            dept, wanted = rule
            employee = next(e for e in employees if e.is_active and e.handle is None and e.department == dept and e.access_level == wanted and 2 <= e.grade <= 8)
        logins.append({
            "username": username,
            "access_level": access_level,
            "employee_id": employee.employee_id if employee else None,
            "display_name": employee.name if employee else "External visitor (no employee record)",
            "email": employee.email if employee else None,
            "department": canon.DEPT_NAME[employee.department] if employee else None,
        })
    return logins


def build() -> Personnel:
    factory = _Factory()
    people = _key_people(factory)
    current_heads = {dept: people[handle] for dept, handle, _, end in canon.DEPARTMENT_HEADS if end is None}

    # Reporting lines for the key people.
    ashworth, tarrow = people["ashworth"], people["tarrow"]
    for handle, person in people.items():
        if handle == "ashworth":
            continue
        if handle == "tarrow" or person.department == "OCH":
            person.manager_id = ashworth.employee_id
        elif current_heads.get(person.department) is person or handle in ("stroud", "sallow", "kalvane", "voss", "doyle", "ferrante"):
            person.manager_id = tarrow.employee_id

    for _, dept, _, headcount in canon.DEPARTMENTS:
        key_members = [p for p in people.values() if p.department == dept and p.is_active]
        generated = _generate_department(factory, dept, headcount, current_heads[dept], key_members)
        for person in key_members:
            if person.manager_id is None:
                managers = [e for e in generated if e.grade in (10, 11)]
                person.manager_id = (managers[0] if managers else current_heads[dept]).employee_id

    former_needed = EMPIRE_FORMER_EMPLOYEES - sum(1 for p in people.values() if not p.is_active)
    _former_employees(factory, former_needed, current_heads)

    employees = factory.employees
    by_id = {e.employee_id: e for e in employees}
    leadership = _leadership(people)
    personnel = Personnel(employees, by_id, people, leadership, [])

    history_rng = stream("personnel-history")
    _key_history(history_rng, people)
    for employee in employees:
        if employee.handle is None:
            employee.history = _generic_history(history_rng, employee, personnel.head_of)
    personnel.logins = _logins(employees)

    active = [e for e in employees if e.is_active]
    assert len(active) == EMPIRE_HEADCOUNT, f"expected {EMPIRE_HEADCOUNT} active employees, got {len(active)}"
    return personnel
