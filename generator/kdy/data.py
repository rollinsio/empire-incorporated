"""Kuat Drive Yards' structured data: people, customers, products, quotes, orders, production and costs."""

from dataclasses import dataclass
from datetime import date, timedelta

from generator.config import AS_OF, KDY_DOMAIN, KDY_HEADCOUNT
from generator.kdy import world
from generator.labels import CONFIDENTIAL, INTERNAL, RESTRICTED
from generator.names import DISTRICTS, FIRST_NAMES, LAST_NAMES, STREETS, email_local_part
from generator.rand import stream
from generator.supply import KDY as KDY_SUPPLIER
from generator.supply import Supply

FORMER_EMPLOYEES = 6
BAYS = ("Bay A", "Bay B", "Bay C", "Bay D", "Bay E", "Bay F")

# The Empire contract, line by line: (product, description, quantity, price Mcr, cost Mcr).
EMPIRE_DEAL_LINES = [
    ("KDY-P-002", "Hull plating section, Starhaven grade", 20_000, 41_200.00, 31_540.00),
    ("KDY-P-006", "Gantry crane hoist, 2000 t, Starhaven slipways", 2_000, 14_600.00, 11_240.00),
    ("KDY-P-008", "Slipway rail segment, straight", 15_000, 5_400.00, 4_200.00),
    ("KDY-P-010", "Dry dock seal assembly, main gate", 1_000, 3_600.00, 2_870.00),
]


@dataclass
class KdyEmployee:
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department: str
    title: str
    grade: int
    manager_id: str | None
    hire_date: date
    salary: int
    access_level: str
    home_address: str
    personal_comlink: str
    status: str = "ACTIVE"
    termination_date: date | None = None
    handle: str | None = None

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"


@dataclass
class KdyData:
    employees: list[KdyEmployee]
    by_handle: dict[str, KdyEmployee]
    customers: list[dict]
    products: list[dict]
    quotes: list[dict]
    quote_lines: list[dict]
    sales_orders: list[dict]
    production_lots: list[dict]
    cost_rates: list[dict]
    contract_margins: list[dict]
    logins: list[dict]

    def active(self, department: str | None = None) -> list[KdyEmployee]:
        return [e for e in self.employees if e.is_active and (department is None or e.department == department)]

    def employee(self, employee_id: str) -> KdyEmployee:
        return next(e for e in self.employees if e.employee_id == employee_id)


# --------------------------------------------------------------------------
# People
# --------------------------------------------------------------------------

def _access_level(department: str, grade: int) -> str:
    if grade >= 10 or (department == "HRS" and grade >= 4):
        return RESTRICTED
    if grade >= 8 or (department in ("FIN", "SAL") and grade >= 4):
        return CONFIDENTIAL
    return INTERNAL


class _People:
    def __init__(self, taken_names: set[tuple[str, str]]):
        self.rng = stream("kdy:people")
        self.taken = taken_names
        self.employees: list[KdyEmployee] = []

    def name(self) -> tuple[str, str]:
        while True:
            pair = (self.rng.choice(FIRST_NAMES), self.rng.choice(LAST_NAMES))
            if pair not in self.taken:
                self.taken.add(pair)
                return pair

    def add(self, first: str, last: str, department: str, title: str, grade: int, hired: date,
            handle: str | None = None, access_level: str | None = None) -> KdyEmployee:
        rng = self.rng
        low, high = world.SALARY_BANDS[grade]
        employee = KdyEmployee(
            employee_id=f"KDY-E-{len(self.employees) + 1:04d}", first_name=first, last_name=last,
            email=f"{email_local_part(first, last)}@{KDY_DOMAIN}", department=department, title=title, grade=grade,
            manager_id=None, hire_date=hired, salary=int(round(rng.uniform(low, high), -2)),
            access_level=access_level or _access_level(department, grade),
            home_address=f"{rng.randint(1, 480)} {rng.choice(STREETS)}, {rng.choice(DISTRICTS)}, Kuat",
            personal_comlink=f"PCL-{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}", handle=handle,
        )
        self.taken.add((first, last))
        self.employees.append(employee)
        return employee


def _people(taken_names: set[tuple[str, str]]) -> tuple[list[KdyEmployee], dict[str, KdyEmployee]]:
    factory = _People(taken_names)
    rng = factory.rng
    by_handle = {handle: factory.add(first, last, dept, title, grade, hired, handle, access_level)
                 for handle, (first, last, dept, title, grade, access_level, hired) in world.KEY_PEOPLE.items()}
    ceo = by_handle["vantress"]
    heads = tuple(world.DEPARTMENT_HEADS.values())
    for handle, person in by_handle.items():
        if person is ceo:
            continue
        person.manager_id = ceo.employee_id if handle in heads else by_handle[world.DEPARTMENT_HEADS[person.department]].employee_id
    for _, code, _, headcount in world.DEPARTMENTS:
        head = by_handle[world.DEPARTMENT_HEADS[code]]
        existing = sum(1 for p in by_handle.values() if p.department == code)
        for n in range(headcount - existing):
            grade = 8 if n == 0 and headcount >= 10 else rng.choice((2, 3, 3, 4, 4, 5, 5, 6, 7))
            first, last = factory.name()
            title = "Team Lead" if grade == 8 else world.TITLES[code][n % len(world.TITLES[code])]
            employee = factory.add(first, last, code, title, grade, AS_OF - timedelta(days=rng.randint(120, 5000)))
            employee.manager_id = head.employee_id
    for _ in range(FORMER_EMPLOYEES):
        code = rng.choice(("ENG", "FAB", "SAL", "QUA"))
        first, last = factory.name()
        hired = AS_OF - timedelta(days=rng.randint(1500, 4000))
        employee = factory.add(first, last, code, world.TITLES[code][0], rng.choice((3, 4, 5)), hired)
        employee.status, employee.termination_date = "DEPARTED", hired + timedelta(days=rng.randint(400, 1300))
        employee.manager_id = by_handle[world.DEPARTMENT_HEADS[code]].employee_id
    assert sum(1 for e in factory.employees if e.is_active) == KDY_HEADCOUNT
    return factory.employees, by_handle


def _logins(employees: list[KdyEmployee]) -> list[dict]:
    logins = []
    for username, access_level, rule in world.LOGINS:
        employee = None
        if rule is not None:
            dept, wanted = rule
            employee = next(e for e in employees if e.is_active and e.handle is None and e.department == dept and e.access_level == wanted)
        logins.append({"username": username, "access_level": access_level, "employee_id": employee.employee_id if employee else None,
                       "display_name": employee.name if employee else "External visitor (no employee record)",
                       "email": employee.email if employee else None,
                       "department": world.DEPT_NAME[employee.department] if employee else None})
    return logins


# --------------------------------------------------------------------------
# Commercial data
# --------------------------------------------------------------------------

def _customers(by_handle: dict[str, KdyEmployee], sales: list[KdyEmployee]) -> list[dict]:
    rows = []
    for n, (customer_id, name, planet, tier, domain) in enumerate(world.CUSTOMERS):
        manager = by_handle["danvik"] if customer_id == world.EMPIRE_CUSTOMER else sales[n % len(sales)]
        rows.append({"customer_id": customer_id, "name": name, "planet": planet, "tier": tier,
                     "account_manager_id": manager.employee_id, "procurement_email": f"procurement@{domain}", "sensitivity": INTERNAL})
    return rows


def _products(rng) -> list[dict]:
    return [{"product_id": pid, "name": name, "category": category, "unit": unit, "list_price_credits": float(price),
             "standard_cost_credits": round(price * share * rng.uniform(0.98, 1.02), 2), "sensitivity": CONFIDENTIAL}
            for pid, name, category, unit, price, share in world.PRODUCTS]


def _empire_quote(by_handle: dict[str, KdyEmployee]) -> tuple[dict, list[dict]]:
    deal = world.EMPIRE_DEAL
    lines = [{"quote_id": deal["quote_id"], "line_no": n, "product_id": pid, "description": description, "quantity": qty,
              "unit_price_credits": round(price * 1e6 / qty, 2), "unit_cost_credits": round(cost * 1e6 / qty, 2), "sensitivity": CONFIDENTIAL}
             for n, (pid, description, qty, price, cost) in enumerate(EMPIRE_DEAL_LINES, start=1)]
    price = round(sum(line[3] for line in EMPIRE_DEAL_LINES), 2)
    cost = round(sum(line[4] for line in EMPIRE_DEAL_LINES), 2)
    assert (price, cost) == (deal["price_mcr"], deal["cost_mcr"])
    assert round((price - cost) / price * 100, 2) == deal["margin_pct"]
    quote = {"quote_id": deal["quote_id"], "customer_id": world.EMPIRE_CUSTOMER, "quote_date": deal["quoted"],
             "valid_until": deal["quoted"] + timedelta(days=60), "status": "WON", "total_price_mcr": price, "total_cost_mcr": cost,
             "margin_pct": deal["margin_pct"], "prepared_by": by_handle["danvik"].employee_id, "approved_by": by_handle["brack"].employee_id,
             "sensitivity": CONFIDENTIAL}
    return quote, lines


def _quotes(rng, customers: list[dict], products: list[dict], by_handle: dict[str, KdyEmployee], sales: list[KdyEmployee]):
    quote, lines = _empire_quote(by_handle)
    quotes = [quote]
    others = [c for c in customers if c["customer_id"] != world.EMPIRE_CUSTOMER]
    for n in range(1, 41):
        customer = others[(n - 1) % len(others)]
        quoted = date(2023, 2, 6) + timedelta(days=rng.randint(0, (AS_OF - date(2023, 2, 6)).days - 20))
        quote_id = f"KDY-Q-{quoted.year}-{n + 100:04d}"
        price_total = cost_total = 0.0
        for line_no, product in enumerate(rng.sample(products, rng.randint(1, 4)), start=1):
            qty = rng.randint(2, 60)
            unit_price = round(product["list_price_credits"] * (1 - rng.uniform(0, 0.12)), 2)
            unit_cost = product["standard_cost_credits"]
            lines.append({"quote_id": quote_id, "line_no": line_no, "product_id": product["product_id"], "description": product["name"],
                          "quantity": qty, "unit_price_credits": unit_price, "unit_cost_credits": unit_cost, "sensitivity": CONFIDENTIAL})
            price_total += qty * unit_price
            cost_total += qty * unit_cost
        status = "OPEN" if (AS_OF - quoted).days < 60 else rng.choice(("WON", "WON", "LOST"))
        quotes.append({"quote_id": quote_id, "customer_id": customer["customer_id"], "quote_date": quoted,
                       "valid_until": quoted + timedelta(days=60), "status": status,
                       "total_price_mcr": round(price_total / 1e6, 2), "total_cost_mcr": round(cost_total / 1e6, 2),
                       "margin_pct": round((price_total - cost_total) / price_total * 100, 2),
                       "prepared_by": rng.choice(sales).employee_id, "approved_by": by_handle["lathe"].employee_id, "sensitivity": CONFIDENTIAL})
    quotes.sort(key=lambda q: (q["quote_date"], q["quote_id"]))
    return quotes, lines


def _sales_orders(rng, empire_supply: Supply, customers: list[dict]) -> list[dict]:
    """Every Empire purchase order placed with KDY becomes a KDY sales order; other customers order too."""
    rows = []
    empire_pos = [po for po in empire_supply.purchase_orders if po["supplier_id"] == KDY_SUPPLIER["supplier_id"] and po["status"] != "CANCELLED"]
    for po in empire_pos:
        margin = round(rng.uniform(18.0, 28.0), 2)
        rows.append({"customer_id": world.EMPIRE_CUSTOMER, "customer_po": po["po_number"], "order_date": po["order_date"] + timedelta(days=1),
                     "value_credits": po["total_credits"], "margin_pct": margin})
    others = [c for c in customers if c["customer_id"] != world.EMPIRE_CUSTOMER]
    for n in range(150):
        customer = rng.choice(others)
        ordered = date(2023, 3, 1) + timedelta(days=rng.randint(0, (AS_OF - date(2023, 3, 1)).days))
        rows.append({"customer_id": customer["customer_id"], "customer_po": f"{customer['name'].split()[0][:3].upper()}-{ordered.year}-{n + 1:04d}",
                     "order_date": ordered, "value_credits": round(rng.uniform(80_000, 9_000_000), 2), "margin_pct": round(rng.uniform(16.0, 34.0), 2)})
    rows.sort(key=lambda r: (r["order_date"], r["customer_po"]))
    orders = []
    for n, row in enumerate(rows, start=1):
        cost = round(row["value_credits"] * (1 - row["margin_pct"] / 100), 2)
        age = (AS_OF - row["order_date"]).days
        orders.append({"so_id": f"KDY-SO-{n:05d}", **row, "cost_credits": cost,
                       "status": "DELIVERED" if age > 180 else ("IN_PRODUCTION" if age > 20 else "ACCEPTED"), "sensitivity": CONFIDENTIAL})
    return orders


def _production_lots(rng, orders: list[dict], supervisors: list[KdyEmployee]) -> list[dict]:
    lots = []
    for order in orders:
        for n in range(1, rng.randint(1, 3) + 1):
            start = order["order_date"] + timedelta(days=rng.randint(5, 40))
            planned = rng.randint(80, 2400)
            done = start + timedelta(days=rng.randint(10, 90))
            finished = done if done <= AS_OF and order["status"] != "ACCEPTED" else None
            lots.append({"lot_id": f"LOT-{order['so_id'][7:]}-{n}", "so_id": order["so_id"], "bay": rng.choice(BAYS),
                         "supervisor_id": rng.choice(supervisors).employee_id, "start_date": min(start, AS_OF), "finish_date": finished,
                         "planned_hours": planned, "actual_hours": round(planned * rng.uniform(0.85, 1.25)) if finished else None,
                         "status": "COMPLETE" if finished else "IN_PROGRESS", "sensitivity": INTERNAL})
    return lots


def _contract_margins(rng, customers: list[dict]) -> list[dict]:
    deal = world.EMPIRE_DEAL
    rows = [{"contract_ref": deal["empire_contract_id"], "customer_id": world.EMPIRE_CUSTOMER, "quote_id": deal["quote_id"],
             "start_date": date(2024, 3, 4), "end_date": date(2027, 3, 31), "revenue_mcr": deal["price_mcr"], "cost_mcr": deal["cost_mcr"],
             "margin_pct": deal["margin_pct"], "walk_away_mcr": deal["walk_away_mcr"],
             "renewal_target_margin_pct": deal["renewal_target_margin_pct"], "sensitivity": CONFIDENTIAL}]
    for customer in customers[1:]:
        revenue = round(rng.uniform(400, 9000), 2)
        margin = round(rng.uniform(18, 31), 2)
        rows.append({"contract_ref": f"KDY-FA-{customer['customer_id'][4:]}", "customer_id": customer["customer_id"], "quote_id": None,
                     "start_date": date(2023, 1, 2) + timedelta(days=rng.randint(0, 700)), "end_date": date(2027, 12, 31),
                     "revenue_mcr": revenue, "cost_mcr": round(revenue * (1 - margin / 100), 2), "margin_pct": margin,
                     "walk_away_mcr": round(revenue * rng.uniform(0.86, 0.93), 2),
                     "renewal_target_margin_pct": world.PRICING_POLICY[customer["tier"]] + 2, "sensitivity": CONFIDENTIAL})
    return rows


def build(empire_supply: Supply, taken_names: set[tuple[str, str]]) -> KdyData:
    rng = stream("kdy:commercial")
    employees, by_handle = _people(taken_names)
    sales = [e for e in employees if e.is_active and e.department == "SAL" and e.handle is None and e.grade >= 4]
    customers = _customers(by_handle, sales)
    products = _products(rng)
    quotes, quote_lines = _quotes(rng, customers, products, by_handle, sales)
    orders = _sales_orders(rng, empire_supply, customers)
    supervisors = [e for e in employees if e.is_active and e.department == "FAB" and e.grade >= 5]
    cost_rates = [{"rate_id": f"CR-{year}-{dept}", "fiscal_year": year, "department_id": world.DEPT_ID[dept], "labour_rate_credits_per_hour": rate,
                   "overhead_pct": overhead, "sensitivity": CONFIDENTIAL} for year, dept, rate, overhead in world.COST_RATES]
    return KdyData(
        employees=employees, by_handle=by_handle, customers=customers, products=products, quotes=quotes, quote_lines=quote_lines,
        sales_orders=orders, production_lots=_production_lots(rng, orders, supervisors), cost_rates=cost_rates,
        contract_margins=_contract_margins(rng, customers), logins=_logins(employees),
    )
