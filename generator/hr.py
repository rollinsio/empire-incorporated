"""Performance reviews: one per employee per annual review cycle."""

from dataclasses import dataclass
from datetime import date

from generator.labels import RESTRICTED
from generator.personnel import Personnel
from generator.rand import stream

REVIEW_CYCLES = (2024, 2025)

# rating, label, weight, salary increase range (%)
RATINGS = (
    (1, "Below expectations", 4, (0.0, 0.0)),
    (2, "Partially meets expectations", 10, (0.0, 1.5)),
    (3, "Meets expectations", 48, (2.0, 3.5)),
    (4, "Exceeds expectations", 30, (3.5, 5.5)),
    (5, "Outstanding", 8, (5.5, 8.0)),
)

STRENGTHS = (
    "Delivers work packages on schedule and keeps stakeholders informed.",
    "Thorough, well-documented engineering analysis.",
    "Mentors junior colleagues and runs effective handovers.",
    "Calm and structured under pressure during integration campaigns.",
    "Builds good working relationships with suppliers.",
    "Spots quality issues early and follows them through to closure.",
    "Clear written reports that management can act on.",
    "Strong command of the station's safety procedures.",
)
DEVELOPMENT = (
    "Delegate more routine tasks to the team.",
    "Raise schedule risks earlier in the weekly review.",
    "Complete the advanced project management course.",
    "Improve estimates for rework effort.",
    "Take on a cross-department integration task next cycle.",
    "Keep task records in the planning system up to date.",
    "Prepare for a team lead role through the leadership programme.",
)


@dataclass
class HrRecords:
    reviews: list[dict]

    def for_employee(self, employee_id: str) -> list[dict]:
        return [r for r in self.reviews if r["employee_id"] == employee_id]


def build(personnel: Personnel) -> HrRecords:
    rng = stream("hr-reviews")
    weights = [weight for _, _, weight, _ in RATINGS]
    reviews = []
    for year in REVIEW_CYCLES:
        review_date = date(year + 1, 2, 16)
        for employee in personnel.employees:
            if employee.hire_date > date(year, 9, 30) or (employee.termination_date and employee.termination_date < review_date):
                continue
            if employee.manager_id is None:
                continue
            rating, label, _, (low, high) = rng.choices(RATINGS, weights=weights, k=1)[0]
            reviews.append({
                "review_id": f"PR-{year}-{employee.employee_id[4:]}",
                "employee_id": employee.employee_id,
                "cycle_year": year,
                "reviewer_id": employee.manager_id,
                "review_date": review_date,
                "rating": rating,
                "rating_label": label,
                "strengths": rng.choice(STRENGTHS),
                "development": rng.choice(DEVELOPMENT),
                "salary_increase_pct": round(rng.uniform(low, high), 1),
                "sensitivity": RESTRICTED,
            })
    return HrRecords(reviews)
