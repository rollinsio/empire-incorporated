"""Experiment scenarios: six themes of the company's work, each asked the same eight kinds of prompt.

Every scenario has one prompt per slot, so a loop is measured on the same mix
in every theme, and every loop on the same prompts:

  fact          a fact from one document; the answer names no person
  person        the answer is a person's name (a scrubbing loop must restore it)
  database      answered from tables alone, by SQL
  aggregate     a count, a maximum or an average
  cross_source  needs two sources together
  over_time     who or what held on a given date, or which revision is approved
  german        the source is a German document
  boundary      the right outcome is a refusal, "not found", or not following
                an instruction planted in a document

Prompts are chosen from the questions the builders offered (each already
grounded in its sources), deterministically, from the pools a scenario names
for each slot. Each prompt says whether personal data is in the prompt and
in the expected answer, for the leakage measurement.
"""

from collections.abc import Callable, Iterable, Mapping

from generator.rand import stream

SLOTS = {
    "fact": "A fact from one document; the answer names no person.",
    "person": "The answer is a person's name.",
    "database": "Answered from tables alone, by SQL.",
    "aggregate": "A count, a maximum or an average.",
    "cross_source": "Needs two sources together.",
    "over_time": "Who or what held on a given date, or which revision is approved.",
    "german": "The source is a German document.",
    "boundary": "The right outcome is a refusal, 'not found', or not following a planted instruction.",
}

SCENARIOS = (
    ("people", "People and HR", "Policies, rosters, reviews and salaries: the most personal data in the company.", {
        "fact": ("business:policy-fact",),
        "person": ("business:roster-manager",),
        "database": ("data:sql-employee-title",),
        "aggregate": ("data:salary-summary", "data:review-summary"),
        "cross_source": ("business:review-reviewer-dept",),
        "over_time": ("data:history-title",),
        "german": ("business:policy-eriadu",),
        "boundary": ("testcases:mislabeled-refuse",),
    }),
    ("procurement", "Procurement and suppliers", "Contracts, purchase orders, deliveries and the supplier in the other tenant.", {
        "fact": ("business:contract-term",),
        "person": ("business:po-approver",),
        "database": ("data:sql-po-status",),
        "aggregate": ("data:top-supplier",),
        "cross_source": ("business:contract-supplier-rating", "comms:kdy-po-total"),
        "over_time": ("data:leadership-on-date",),
        "german": ("comms:eriadu-delivery",),
        "boundary": ("kdy:isolation-empire-asks",),
    }),
    ("engineering", "Engineering and quality", "Specifications, revisions, tests, inspections and non-conformances.", {
        "fact": ("technical:spec-value",),
        "person": ("comms:ncr-raised-by", "comms:test-report-tester"),
        "database": ("data:sql-requirement",),
        "aggregate": ("technical:inspection-count",),
        "cross_source": ("technical:spec-approver-dept",),
        "over_time": ("testcases:approved-spec",),
        "german": ("technical:test-measured",),
        "boundary": ("testcases:injection",),
    }),
    ("programs", "Programs and leadership", "Status reports, minutes, budgets, milestones and who led what when.", {
        "fact": ("business:status-overall",),
        "person": ("business:minutes-action",),
        "database": ("data:sql-milestone-forecast",),
        "aggregate": ("business:budget-year-total",),
        "cross_source": ("comms:wp-progress", "business:status-milestone"),
        "over_time": ("business:minutes-chair", "comms:program-director-change"),
        "german": ("business:eriadu-stall",),
        "boundary": ("data:access-budget",),
    }),
    ("communications", "Mail, chat, calendar and tickets", "What people wrote to each other, and what they asked the helpdesk.", {
        "fact": ("comms:notice",),
        "person": ("comms:chat-top-poster",),
        "database": ("data:sql-document-created",),
        "aggregate": ("comms:chat-count",),
        "cross_source": ("comms:sender-dept",),
        "over_time": ("comms:review-organizer",),
        "german": ("comms:ticket-assignee", "comms:chat-count"),
        "boundary": ("comms:no-answer",),
    }),
    ("operations", "Operations and facilities", "Construction progress, sensors, facility incidents and messy files.", {
        "fact": ("messy:wrong-extension",),
        "person": ("data:incident-reporter",),
        "database": ("data:reactor-peak",),
        "aggregate": ("data:zone-stall",),
        "cross_source": ("data:reactor-peak-incident", "comms:ticket-incident"),
        "over_time": ("data:leadership-handover",),
        "german": ("messy:legacy-encoding",),
        "boundary": ("messy:empty", "messy:corrupt"),
    }),
)


def _answered(question: Mapping) -> bool:
    return question["expected"]["type"] == "answer"


def _german(question: Mapping) -> bool:
    return any(source.get("language") == "de" for source in question["sources"])


def _rules(names: frozenset[str]) -> dict[str, Callable[[Mapping], bool]]:
    def names_person(text: str | None) -> bool:
        return bool(text) and any(name in text for name in names)

    return {
        "fact": lambda q: _answered(q) and not names_person(q["expected"]["answer"]),
        "person": lambda q: _answered(q) and names_person(q["expected"]["answer"]),
        "database": lambda q: _answered(q) and bool(q["sources"]) and all(s["kind"] in ("table", "view") for s in q["sources"]),
        "aggregate": _answered,
        "cross_source": lambda q: _answered(q) and len(q["sources"]) >= 2,
        "over_time": _answered,
        "german": lambda q: _answered(q) and _german(q),
        "boundary": lambda q: not _answered(q),
    }


def _personal(question: Mapping, names: frozenset[str], values: frozenset[str]) -> dict:
    """Which personal data the prompt and the expected answer hold, by kind."""

    def found(text: str | None) -> list[str]:
        if not text:
            return []
        kinds = ["name"] if any(name in text for name in names) else []
        return kinds + (["personal_value"] if any(value in text for value in values) else [])

    return {"in_prompt": found(question["question"]), "in_answer": found(question["expected"]["answer"])}


def select(offered: Iterable[Mapping], resolve: Callable[[Mapping], dict], names: frozenset[str],
           values: frozenset[str]) -> dict:
    """One prompt per slot per scenario, each resolved to the login that asks it."""
    by_pool: dict[str, list[Mapping]] = {}
    for question in offered:
        by_pool.setdefault(question["pool"], []).append(question)
    rules = _rules(names)
    taken: set[str] = set()
    scenarios = []
    for number, (key, title, description, slots) in enumerate(SCENARIOS, start=1):
        prompts = []
        for slot in SLOTS:
            candidates = [q for pool in slots[slot] for q in by_pool.get(pool, ()) if rules[slot](q) and q["question"] not in taken]
            if not candidates:
                raise ValueError(f"scenario {key}: no question fits slot {slot} from {slots[slot]}")
            question = resolve(stream(f"scenarios:{key}:{slot}").choice(candidates))
            taken.add(question["question"])
            prompts.append({
                "id": f"S{number}-{len(prompts) + 1}", "slot": slot,
                **{k: v for k, v in question.items() if k != "pool"},
                "pii": _personal(question, names, values),
                "pool": question["pool"],
            })
        scenarios.append({"id": f"S{number}", "key": key, "title": title, "description": description, "prompts": prompts})
    return {"slots": SLOTS, "scenarios": scenarios}
