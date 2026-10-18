"""The four sensitivity labels and the rule for who may see what."""

PUBLIC = "PUBLIC"
INTERNAL = "INTERNAL"
CONFIDENTIAL = "CONFIDENTIAL"
RESTRICTED = "RESTRICTED"

LABELS = (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED)
RANK = {label: rank for rank, label in enumerate(LABELS)}

DISPLAY = {
    "en": {
        PUBLIC: "PUBLIC",
        INTERNAL: "INTERNAL",
        CONFIDENTIAL: "CONFIDENTIAL",
        RESTRICTED: "RESTRICTED",
    },
    "de": {
        PUBLIC: "ÖFFENTLICH",
        INTERNAL: "INTERN",
        CONFIDENTIAL: "VERTRAULICH",
        RESTRICTED: "STRENG VERTRAULICH",
    },
}

DESCRIPTIONS = {
    PUBLIC: "Approved for release outside the company.",
    INTERNAL: "Any employee may see it; not for release outside the company.",
    CONFIDENTIAL: "Business-sensitive: budgets, contract prices, supplier terms and cost data. Employees with a business need.",
    RESTRICTED: "Personal data: salaries, performance reviews and home contact details. Personnel staff and line management only.",
}


def may_see(access_level: str, sensitivity: str) -> bool:
    return RANK[access_level] >= RANK[sensitivity]
