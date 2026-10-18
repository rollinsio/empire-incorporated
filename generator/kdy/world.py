"""The fixed facts of Kuat Drive Yards. Everything here is invented."""

from datetime import date

from generator.labels import CONFIDENTIAL, INTERNAL, RESTRICTED

COMPANY = "Kuat Drive Yards"
HQ = "Kuat City, Kuat"

DEPARTMENTS = [
    # id, code, name, headcount
    ("K01", "EXE", "Executive Office", 6),
    ("K02", "SAL", "Sales & Key Accounts", 14),
    ("K03", "ENG", "Engineering", 30),
    ("K04", "FAB", "Fabrication", 50),
    ("K05", "QUA", "Quality", 12),
    ("K06", "FIN", "Finance", 10),
    ("K07", "HRS", "People & Culture", 6),
    ("K08", "PRC", "Procurement", 8),
    ("K09", "LOG", "Logistics", 4),
]
DEPT_ID = {code: dept_id for dept_id, code, _, _ in DEPARTMENTS}
DEPT_NAME = {code: name for _, code, name, _ in DEPARTMENTS}
DEPT_NAME_BY_ID = {dept_id: name for dept_id, _, name, _ in DEPARTMENTS}

TITLES = {
    "EXE": ("Executive Assistant", "Strategy Analyst"),
    "SAL": ("Sales Coordinator", "Account Manager", "Bid Manager"),
    "ENG": ("Design Engineer", "Structural Analyst", "Production Engineer"),
    "FAB": ("Plater", "Welder", "Crane Fitter", "Shift Supervisor"),
    "QUA": ("Quality Inspector", "Quality Engineer"),
    "FIN": ("Cost Accountant", "Financial Analyst"),
    "HRS": ("People Partner", "Payroll Specialist"),
    "PRC": ("Buyer", "Supplier Quality Engineer"),
    "LOG": ("Logistics Planner", "Dispatch Coordinator"),
}

SALARY_BANDS = {
    1: (24_000, 30_000), 2: (29_000, 36_000), 3: (35_000, 43_000), 4: (42_000, 52_000), 5: (50_000, 62_000),
    6: (60_000, 74_000), 7: (72_000, 88_000), 8: (86_000, 104_000), 9: (100_000, 124_000), 10: (120_000, 150_000),
    11: (145_000, 185_000), 12: (220_000, 300_000),
}

# handle: first, last, dept, title, grade, access level, hire date
KEY_PEOPLE = {
    "vantress": ("Aurelia", "Vantress", "EXE", "Chief Executive Officer", 12, RESTRICTED, date(2009, 2, 2)),
    "brack": ("Hollis", "Brack", "FIN", "Chief Financial Officer", 12, RESTRICTED, date(2012, 5, 14)),
    "lathe": ("Severin", "Lathe", "SAL", "Head of Sales & Key Accounts", 11, RESTRICTED, date(2014, 9, 1)),
    "danvik": ("Merel", "Danvik", "SAL", "Key Account Manager, Empire Incorporated", 8, CONFIDENTIAL, date(2018, 3, 12)),
    "halcrow": ("Ida", "Halcrow", "ENG", "Director of Engineering", 11, RESTRICTED, date(2011, 7, 4)),
    "marsh": ("Tobin", "Marsh", "FAB", "Director of Fabrication", 11, RESTRICTED, date(2010, 1, 18)),
    "quint": ("Ysolde", "Quint", "QUA", "Head of Quality", 10, RESTRICTED, date(2016, 6, 6)),
    "corbel": ("Nadine", "Corbel", "HRS", "Head of People & Culture", 10, RESTRICTED, date(2017, 10, 2)),
    "fenner": ("Jory", "Fenner", "PRC", "Head of Procurement", 10, RESTRICTED, date(2015, 4, 20)),
    "albright": ("Cass", "Albright", "LOG", "Logistics Lead", 9, CONFIDENTIAL, date(2019, 8, 5)),
}
DEPARTMENT_HEADS = {"EXE": "vantress", "SAL": "lathe", "ENG": "halcrow", "FAB": "marsh", "QUA": "quint",
                    "FIN": "brack", "HRS": "corbel", "PRC": "fenner", "LOG": "albright"}

CUSTOMERS = [
    # id, name, planet, tier, email domain
    ("CUS-001", "Empire Incorporated", "Coruscant", "KEY", "empire-inc.example"),
    ("CUS-002", "Brentaal Freight Lines", "Brentaal", "KEY", "brentaal-freight-lines.example"),
    ("CUS-003", "Chandrila Transit Authority", "Chandrila", "STANDARD", "chandrila-transit.example"),
    ("CUS-004", "Sluis Van Orbital Works", "Sluis Van", "STANDARD", "sluis-van-orbital-works.example"),
    ("CUS-005", "Alsakan Ferry Company", "Alsakan", "STANDARD", "alsakan-ferry.example"),
    ("CUS-006", "Fondor Shipyards", "Fondor", "KEY", "fondor-shipyards.example"),
    ("CUS-007", "Corellia Harbour Authority", "Corellia", "STANDARD", "corellia-harbour.example"),
]
EMPIRE_CUSTOMER = "CUS-001"

# id, name, category, unit, public list price (credits), standard cost as a share of list price
PRODUCTS = [
    ("KDY-P-001", "Hull plating section, type 1", "Hull", "ea", 88_000, 0.74),
    ("KDY-P-002", "Hull plating section, type 2", "Hull", "ea", 94_000, 0.73),
    ("KDY-P-003", "Hull plating section, type 3 equatorial", "Hull", "ea", 104_000, 0.75),
    ("KDY-P-004", "Hull plating section, type 4 polar", "Hull", "ea", 112_000, 0.76),
    ("KDY-P-005", "Gantry crane hoist, 800 t", "Cranes", "ea", 420_000, 0.71),
    ("KDY-P-006", "Gantry crane hoist, 2000 t", "Cranes", "ea", 610_000, 0.72),
    ("KDY-P-007", "Gantry crane hoist, 4000 t", "Cranes", "ea", 760_000, 0.73),
    ("KDY-P-008", "Slipway rail segment, straight", "Shipyard", "ea", 31_000, 0.69),
    ("KDY-P-009", "Slipway rail segment, curved", "Shipyard", "ea", 36_000, 0.70),
    ("KDY-P-010", "Dry dock seal assembly, main gate", "Shipyard", "ea", 300_000, 0.77),
    ("KDY-P-011", "Freighter hull module, 40 m", "Hull", "ea", 1_450_000, 0.78),
    ("KDY-P-012", "Ferry passenger deck module", "Hull", "ea", 980_000, 0.76),
    ("KDY-P-013", "Docking clamp assembly", "Shipyard", "ea", 145_000, 0.71),
    ("KDY-P-014", "Transit tube section, 120 m", "Infrastructure", "ea", 260_000, 0.74),
]

# The Empire contract as KDY sees it. Empire knows only the contract value; everything else is KDY-internal.
EMPIRE_DEAL = {
    "quote_id": "KDY-Q-2024-0031",
    "empire_contract_id": "CTR-2024-0117",
    "price_mcr": 64_800.00,
    "cost_mcr": 49_850.00,
    "margin_pct": 23.07,
    "walk_away_mcr": 58_300.00,
    "renewal_target_margin_pct": 26.75,
    "quoted": date(2024, 1, 22),
    "won": date(2024, 2, 26),
}
PRICING_POLICY = {"KEY": 22.0, "STANDARD": 28.0, "floor": 15.0}
COST_RATES = [
    # year, department, labour rate (credits per hour), overhead %
    (2024, "FAB", 388.00, 36.0), (2024, "ENG", 515.00, 31.0), (2024, "QUA", 402.00, 29.0),
    (2025, "FAB", 401.00, 37.0), (2025, "ENG", 532.00, 31.5), (2025, "QUA", 409.00, 29.5),
    (2026, "FAB", 412.50, 38.0), (2026, "ENG", 548.00, 32.0), (2026, "QUA", 417.00, 30.0),
]

# Facts that exist only in KDY's tenant. Empire's bucket and database must never contain them.
ISOLATION_FACTS = {
    "empire_margin": f"{EMPIRE_DEAL['margin_pct']:.2f}%",
    "empire_cost": f"{EMPIRE_DEAL['cost_mcr']:,.2f}",
    "walk_away": f"{EMPIRE_DEAL['walk_away_mcr']:,.2f}",
    "renewal_target": f"{EMPIRE_DEAL['renewal_target_margin_pct']}%",
    "fabrication_rate": "412.50",
}

LOGINS = [
    ("kdy.visitor.public", "PUBLIC", None),
    ("kdy.staff.internal", INTERNAL, ("FAB", INTERNAL)),
    ("kdy.analyst.confidential", CONFIDENTIAL, ("FIN", CONFIDENTIAL)),
    ("kdy.hr.restricted", RESTRICTED, ("HRS", RESTRICTED)),
]
