"""Ground-truth questions answered from Empire Incorporated's structured data alone.

No document builder owns these: leadership and job history over time,
analytics over the time series, access-control checks on database rows, and
questions whose answer does not exist anywhere in the dataset.
"""

from datetime import timedelta

from generator import canon
from generator.config import AS_OF
from generator.context import Context
from generator.facilities import PEAK_INCIDENT
from generator.labels import CONFIDENTIAL, INTERNAL, RESTRICTED
from generator.personnel import history_id
from generator.telemetry import PEAK_AT, PEAK_SENSOR, PEAK_VALUE, STALL_END, STALL_START, STALLED_ZONE

PROGRAM_NAMES = {program_id: name for program_id, _, name, *_ in canon.PROGRAMS}
ROLE_NAMES = {"HEAD": "headed", "PROGRAM_DIRECTOR": "was program director of", "EXECUTIVE_SPONSOR": "was executive sponsor of"}


def _entity_name(row: dict) -> str:
    if row["entity_type"] == "DEPARTMENT":
        return next(name for dept_id, _, name, _ in canon.DEPARTMENTS if dept_id == row["entity_id"])
    return PROGRAM_NAMES[row["entity_id"]]


# --------------------------------------------------------------------------
# Temporal
# --------------------------------------------------------------------------

def _leadership_questions(ctx: Context) -> None:
    rows = ctx.personnel.leadership
    changing = {(r["entity_id"], r["role"]) for r in rows if r["end_date"] is not None}
    for row in rows:
        if (row["entity_id"], row["role"]) not in changing:
            continue
        person = ctx.employee(row["employee_id"])
        end = row["end_date"] or AS_OF
        start = max(row["start_date"], end - timedelta(days=400))
        on = start + (end - start) / 2
        verb = ROLE_NAMES[row["role"]]
        ctx.truth.offer_question(
            pool="data:leadership-on-date", category="temporal",
            question=f"Who {verb} {_entity_name(row)} on {on.isoformat()}?", answer=person.name, must_include=[person.last_name],
            sources=[ctx.truth.row_source("leadership", INTERNAL, leadership_id=row["leadership_id"]),
                     ctx.truth.row_source("employees", INTERNAL, employee_id=person.employee_id)],
        )
        if row["end_date"] is not None:
            successor = next(r for r in rows if (r["entity_id"], r["role"]) == (row["entity_id"], row["role"]) and r["start_date"] > row["start_date"])
            new = ctx.employee(successor["employee_id"])
            ctx.truth.offer_question(
                pool="data:leadership-handover", category="temporal",
                question=f"When did {person.name} stop being the person who {verb} {_entity_name(row)}, and who took over?",
                answer=f"{row['end_date'].isoformat()}; {new.name} from {successor['start_date'].isoformat()}",
                must_include=[row["end_date"].isoformat(), new.last_name],
                sources=[ctx.truth.row_source("leadership", INTERNAL, leadership_id=row["leadership_id"]),
                         ctx.truth.row_source("leadership", INTERNAL, leadership_id=successor["leadership_id"]),
                         ctx.truth.row_source("employees", INTERNAL, employee_id=new.employee_id)],
            )


def _history_questions(ctx: Context) -> None:
    for employee in ctx.personnel.employees:
        if employee.handle is not None or len(employee.history) < 2:
            continue
        for n, (before, after) in enumerate(zip(employee.history, employee.history[1:]), start=1):
            on = before.start + (after.start - before.start) / 2
            row = ctx.truth.row_source("employment_history", INTERNAL, history_id=history_id(employee.employee_id, n))
            if after.event == "TRANSFER":
                dept_row = ctx.truth.row_source("departments", INTERNAL, department_id=canon.DEPT_ID[before.department])
                ctx.truth.offer_question(
                    pool="data:history-department", category="temporal",
                    question=f"Which department did {employee.name} ({employee.employee_id}) work in on {on.isoformat()}?",
                    answer=canon.DEPT_NAME[before.department], sources=[row, dept_row],
                )
            elif after.event == "PROMOTION" and before.title != after.title:
                ctx.truth.offer_question(
                    pool="data:history-title", category="temporal",
                    question=f"What was {employee.name}'s ({employee.employee_id}) job title on {on.isoformat()}?",
                    answer=before.title, sources=[row],
                )


# --------------------------------------------------------------------------
# Analytics
# --------------------------------------------------------------------------

def _analytics_questions(ctx: Context) -> None:
    ctx.truth.offer_question(
        pool="data:zone-stall", category="analytics",
        question=f"Which construction zone made the least progress between {STALL_START.isoformat()} and {STALL_END.isoformat()}?",
        answer=STALLED_ZONE, sources=[ctx.truth.row_source("zone_progress", INTERNAL, zone_code=STALLED_ZONE)],
        notes="Zone Z17 stalled for the whole quarter (quadanium beam shortage).",
    )
    peak_row = ctx.truth.row_source("sensor_readings", CONFIDENTIAL, sensor_id=PEAK_SENSOR, reading_at=PEAK_AT)
    ctx.truth.offer_question(
        pool="data:reactor-peak", category="analytics",
        question=f"When did sensor {PEAK_SENSOR} record its highest reactor core temperature, and what was the value?",
        answer=f"{PEAK_AT:%Y-%m-%d %H:%M} UTC, {PEAK_VALUE} K", must_include=[PEAK_AT.date().isoformat(), str(PEAK_VALUE)], sources=[peak_row],
    )
    ctx.truth.offer_question(
        pool="data:reactor-peak-incident", category="cross_source",
        question="Which facility incident was opened on the day the reactor core temperature reached its highest reading?",
        answer=PEAK_INCIDENT["incident_id"],
        sources=[peak_row, ctx.truth.row_source("facility_incidents", INTERNAL, incident_id=PEAK_INCIDENT["incident_id"])],
    )
    for dept_id, _code, name, headcount in canon.DEPARTMENTS:
        ctx.truth.offer_question(
            pool="data:department-headcount", category="analytics",
            question=f"How many active employees does {name} have?", answer=str(headcount),
            sources=[ctx.truth.row_source("departments", INTERNAL, department_id=dept_id)],
        )
    counts: dict[str, int] = {}
    for po in ctx.supply.purchase_orders:
        counts[po["supplier_id"]] = counts.get(po["supplier_id"], 0) + 1
    top = max(sorted(counts), key=lambda supplier_id: counts[supplier_id])
    supplier = next(s for s in ctx.supply.suppliers if s["supplier_id"] == top)
    ctx.truth.offer_question(
        pool="data:top-supplier", category="analytics",
        question="Which supplier received the most purchase orders?", answer=f"{supplier['name']} ({counts[top]} orders)",
        must_include=[supplier["name"]],
        sources=[ctx.truth.row_source("suppliers", INTERNAL, supplier_id=top), ctx.truth.row_source("purchase_orders", CONFIDENTIAL, supplier_id=top)],
    )


# --------------------------------------------------------------------------
# Access control on database rows
# --------------------------------------------------------------------------

def _access_questions(ctx: Context) -> None:
    program = next(p for p in ctx.programs.programs if p["program_id"] == canon.MAIN_PROGRAM)
    budget = program["budget_mcr"]
    program_row = ctx.truth.row_source("programs", CONFIDENTIAL, program_id=canon.MAIN_PROGRAM)
    question = f"What is the total budget of the {canon.STATION} program?"
    ctx.truth.offer_question(pool="data:access-budget", category="access_control", asked_as="staff.internal", question=question,
                             answer=None, expected_type="refuse", sources=[program_row], must_not_include=[f"{budget:,}", str(budget)])
    ctx.truth.offer_question(pool="data:access-budget", category="access_control", asked_as="analyst.confidential", question=question,
                             answer=f"{budget:,} Mcr", must_include=[str(budget)], sources=[program_row])
    kestrel = ctx.person("kestrel")
    salary_row = ctx.truth.row_source("employee_private", RESTRICTED, employee_id=kestrel.employee_id)
    question = f"What is {kestrel.name}'s current salary?"
    ctx.truth.offer_question(pool="data:access-salary", category="access_control", asked_as="analyst.confidential", question=question,
                             answer=None, expected_type="refuse", sources=[salary_row], must_not_include=[str(kestrel.salary), f"{kestrel.salary:,}"])
    ctx.truth.offer_question(pool="data:access-salary", category="access_control", asked_as="hr.restricted", question=question,
                             answer=f"{kestrel.salary:,} credits", must_include=[str(kestrel.salary)], sources=[salary_row])
    employee_row = ctx.truth.row_source("employees", INTERNAL, employee_id=kestrel.employee_id)
    question = f"What is {kestrel.name}'s comm extension?"
    ctx.truth.offer_question(pool="data:access-extension", category="access_control", asked_as="visitor.public", question=question,
                             answer=None, expected_type="refuse", sources=[employee_row], must_not_include=[kestrel.comm_extension])
    ctx.truth.offer_question(pool="data:access-extension", category="access_control", asked_as="staff.internal", question=question,
                             answer=kestrel.comm_extension, sources=[employee_row])


# --------------------------------------------------------------------------
# No answer
# --------------------------------------------------------------------------

NO_ANSWER = (
    "What is the approved specification number for the casino deck on Starhaven?",
    "What was the result of test report SHV-HR-TR-9999?",
    "How much did Empire Incorporated pay Kuat Drive Yards in fiscal year 2019?",
    "Who is the head of the Marketing department?",
    "What is the construction progress of Zone Z25?",
    "When is the second Starhaven station scheduled to start construction?",
    "What is Brenna Tolle's favourite food?",
    "Which supplier delivers the Starhaven water slides?",
)


def _no_answer_questions(ctx: Context) -> None:
    for question in NO_ANSWER:
        ctx.truth.offer_question(pool="data:no-answer", category="no_answer", question=question, answer=None,
                                 expected_type="not_found", sources=[], asked_as="hr.restricted")


def build(ctx: Context) -> None:
    _leadership_questions(ctx)
    _history_questions(ctx)
    _analytics_questions(ctx)
    _access_questions(ctx)
    _no_answer_questions(ctx)


def reverse_isolation_facts(ctx: Context) -> dict[str, list[str]]:
    """Empire-only facts that Kuat Drive Yards users ask for; they must come back as "not found"."""
    program = next(p for p in ctx.programs.programs if p["program_id"] == canon.MAIN_PROGRAM)
    kestrel = ctx.person("kestrel")
    approver = ctx.employee(ctx.engineering.by_code["HR-RCV"].approver_id)
    return {
        f"What is the total budget of Empire Incorporated's {canon.STATION} program?": [f"{program['budget_mcr']:,}", str(program["budget_mcr"])],
        f"What is {kestrel.name}'s salary at Empire Incorporated?": [str(kestrel.salary), f"{kestrel.salary:,}"],
        "Who approved Empire Incorporated's reactor core vessel specification SHV-HR-SPEC-0002?": [approver.name],
        f"When does Empire Incorporated plan the first resident crew move-in on {canon.STATION}?": ["2026-11-16", "2026-11-02"],
    }

