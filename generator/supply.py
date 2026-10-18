"""Materials, suppliers, contracts, purchase orders and inventory."""

from dataclasses import dataclass
from datetime import date, timedelta

from generator import canon
from generator.config import AS_OF, KDY_DOMAIN
from generator.labels import CONFIDENTIAL, INTERNAL
from generator.names import FIRST_NAMES, LAST_NAMES, email_local_part
from generator.personnel import Personnel
from generator.programs import Programs
from generator.rand import stream

# The supplier whose own internal data lives in a separate tenant (see generator/kdy/).
KDY = {
    "supplier_id": "SUP-001",
    "name": "Kuat Drive Yards",
    "domain": KDY_DOMAIN,
    "account_manager": ("Merel", "Danvik"),
    "contract_id": "CTR-2024-0117",
    "contract_title": "Starhaven hull plating and gantry crane assemblies",
    "contract_value_mcr": 64_800.0,
    "contract_start": date(2024, 3, 4),
    "contract_end": date(2027, 3, 31),
    "systems": ("SF", "SY"),
}

# (category, base name, unit, cost low, cost high, strategic, hazardous, system, variants)
MATERIAL_BASES = [
    ("Structural", "Durasteel plate", "t", 1800, 4200, False, False, "SF", ["grade A", "grade B", "grade C", "grade D marine", "grade E heavy", "grade F ultra"]),
    ("Structural", "Quadanium steel beam", "t", 2600, 6100, False, False, "SF", ["60 m", "90 m", "120 m", "140 m"]),
    ("Structural", "Hull plating section", "ea", 41000, 96000, False, False, "SF", ["type 1", "type 2", "type 3 equatorial", "type 4 polar"]),
    ("Structural", "Transparisteel viewport panel", "ea", 8200, 31000, False, False, "HA", ["small", "medium", "observation deck"]),
    ("Structural", "Carbon-composite truss", "ea", 900, 3800, False, False, "SF", ["light", "heavy"]),
    ("Fasteners", "Hull fastener kit", "kit", 120, 640, False, False, "SF", ["M40", "M60", "M90", "M120"]),
    ("Fasteners", "Structural bolt set", "set", 60, 300, False, False, "SF", ["class 8", "class 10", "class 12"]),
    ("Power", "Power coupling", "ea", 15000, 88000, False, False, "PD", ["10 MA", "30 MA", "60 MA", "90 MA"]),
    ("Power", "Superconducting bus conduit", "m", 400, 2100, False, False, "PD", ["class 4", "class 5", "class 6"]),
    ("Power", "Zone substation breaker", "ea", 3100, 12000, False, False, "PD", ["standard", "fast-trip"]),
    ("Power", "Backup generator module", "ea", 210000, 480000, False, False, "PD", ["0.5 TW", "1 TW", "2 TW"]),
    ("Power", "Storage battery module", "ea", 64000, 150000, False, True, "PD", ["20 GWh", "40 GWh"]),
    ("Solar", "Solar collector panel", "ea", 22000, 61000, False, False, "SA", ["standard", "high-efficiency"]),
    ("Solar", "Tracking drive motor", "ea", 8800, 24000, False, False, "SA", ["standard"]),
    ("Reactor", "Hypermatter fuel, stabilized", "kg", 92000, 160000, True, True, "HR", ["batch grade I", "batch grade II"]),
    ("Reactor", "Containment field emitter", "ea", 380000, 940000, True, False, "HR", ["mk II", "mk III"]),
    ("Reactor", "Fuel injector cartridge", "ea", 24000, 61000, False, True, "HR", ["standard", "high-flow"]),
    ("Reactor", "Coolant, cryogenic", "m³", 300, 1200, False, True, "HR", ["type K", "type L"]),
    ("Thermal", "Heat exchanger core", "ea", 51000, 140000, False, False, "TX", ["16-stack", "32-stack"]),
    ("Thermal", "Radiator fin panel", "ea", 2200, 7800, False, False, "TX", ["1 m²", "4 m²", "9 m²"]),
    ("Thermal", "Coolant pump", "ea", 31000, 88000, False, False, "TX", ["40 m³/s", "80 m³/s"]),
    ("Propulsion", "Sublight ion engine module", "ea", 410000, 1100000, True, False, "PR", ["standard"]),
    ("Propulsion", "Station-keeping thruster nozzle", "ea", 18000, 52000, False, False, "PR", ["400 kN", "1200 kN"]),
    ("Propulsion", "Gyroscope rotor assembly", "ea", 160000, 420000, True, False, "PR", ["standard"]),
    ("Hangar", "Cargo shuttle cradle segment", "ea", 74000, 210000, False, False, "HB", ["4-craft", "8-craft"]),
    ("Hangar", "Magnetic containment field generator", "ea", 130000, 360000, False, False, "HB", ["bay", "docking"]),
    ("Hangar", "Deck plating, anti-slip", "m²", 80, 260, False, False, "HB", ["standard"]),
    ("Shipyard", "Gantry crane hoist", "ea", 270000, 690000, True, False, "SY", ["800 t", "2000 t", "4000 t"]),
    ("Shipyard", "Slipway rail segment", "ea", 12000, 34000, False, False, "SY", ["straight", "curved"]),
    ("Shipyard", "Dry dock seal assembly", "ea", 120000, 310000, False, False, "SY", ["main gate", "service hatch"]),
    ("Shipyard", "Hull coating, marine-grade", "l", 40, 160, False, True, "SY", ["primer", "topcoat"]),
    ("Electronics", "Computer core processing node", "ea", 21000, 64000, False, False, "CN", ["gen 7", "gen 8"]),
    ("Electronics", "Data backbone switch", "ea", 9000, 28000, False, False, "CN", ["48-port", "96-port"]),
    ("Electronics", "Maintenance port module", "ea", 300, 900, False, False, "CN", ["standard", "ruggedized"]),
    ("Electronics", "Sensor array module", "ea", 5200, 19000, False, False, "CN", ["thermal", "radiation", "pressure"]),
    ("Electronics", "HoloNet transceiver board", "ea", 44000, 120000, False, False, "CM", ["standard"]),
    ("Electronics", "Traffic routing switch card", "ea", 31000, 72000, False, False, "CM", ["standard"]),
    ("Life support", "Atmosphere scrubber cartridge", "ea", 140, 520, False, False, "LS", ["CO2", "trace"]),
    ("Life support", "Water reclamation membrane", "ea", 600, 2400, False, False, "LS", ["standard", "high-flux"]),
    ("Life support", "Gravity plate", "ea", 7200, 21000, False, False, "LS", ["1 m²", "4 m²"]),
    ("Habitation", "Medical supply kit", "kit", 220, 610, False, False, "HA", ["standard", "surgical"]),
    ("Habitation", "Crew berth module", "ea", 2600, 7100, False, False, "HA", ["single", "family"]),
    ("Habitation", "Galley equipment set", "set", 9000, 26000, False, False, "HA", ["standard"]),
    ("Habitation", "Classroom furniture set", "set", 1400, 3900, False, False, "HA", ["primary", "secondary"]),
    ("Agriculture", "Hydroponic grow tray", "ea", 90, 340, False, False, "AG", ["shallow", "deep"]),
    ("Agriculture", "Nutrient concentrate", "l", 12, 48, False, False, "AG", ["leafy greens", "fruiting crops"]),
    ("Agriculture", "LED grow light fixture", "ea", 600, 1900, False, False, "AG", ["600 W", "1000 W"]),
    ("Agriculture", "Seed stock", "kg", 300, 2400, False, False, "AG", ["vegetables", "grains", "herbs"]),
    ("Waste", "Compactor wall drive", "ea", 52000, 130000, False, False, "WM", ["standard"]),
    ("Waste", "Recycling sorter module", "ea", 38000, 97000, False, False, "WM", ["metals", "polymers"]),
    ("Transit", "Turbolift car assembly", "ea", 180000, 420000, False, False, "TR", ["12-person", "40-person"]),
    ("Transit", "Tram bogie", "ea", 46000, 110000, False, False, "TR", ["powered", "trailer"]),
    ("Transit", "Tram rail segment", "ea", 3800, 9400, False, False, "TR", ["40 m", "120 m"]),
    ("Research", "Laboratory fume hood", "ea", 9800, 24000, False, False, "RL", ["standard", "walk-in"]),
    ("Research", "Cleanroom filter unit", "ea", 2400, 7100, False, False, "RL", ["class 5", "class 6"]),
    ("Research", "Telescope mirror segment", "ea", 1200000, 2600000, True, False, "RL", ["inner ring", "outer ring"]),
    ("Consumables", "Welding consumables pack", "pack", 40, 180, False, False, "SF", ["standard", "heavy"]),
    ("Consumables", "Protective suit, vacuum rated", "ea", 1400, 3900, False, False, "SF", ["standard", "heavy"]),
]

SUPPLIERS = [
    ("Kuat Drive Yards", "Kuat"), ("Lianna Orbital Systems", "Lianna"), ("Rendili StarDrive", "Rendili"),
    ("Kuat Precision Instruments", "Kuat"), ("Axxila Power Cells", "Axxila"), ("Cygnus Spaceworks", "Fondor"),
    ("Fabritech", "Coruscant"), ("Abregado Droid Works", "Abregado-rae"), ("Telgorn Corporation", "Columex"),
    ("Carbanti United Electronics", "Coruscant"), ("SoroSuub Corporation", "Sullust"), ("Uulshos Manufacturing", "Coruscant"),
    ("Fondor Foundry Collective", "Fondor"), ("Fondor Shipyards", "Fondor"), ("Sluis Van Orbital Works", "Sluis Van"),
    ("Corulag Precision Optics", "Corulag"), ("Eriadu Steelworks", "Eriadu"), ("Brentaal Logistics Guild", "Brentaal"),
    ("Mekuun Fabrication", "Byss"), ("Chiewab Medical", "Coruscant"), ("Rothana Heavy Cranes", "Rothana"),
    ("Kalist Mining Combine", "Kalist"), ("Bespin Gas Consortium", "Bespin"), ("Naboo Hydroponic Supply", "Naboo"),
    ("Mustafar Refinery Cooperative", "Mustafar"), ("Ord Mantell Salvage & Supply", "Ord Mantell"),
    ("Anaxes Turbolift Company", "Anaxes"), ("Carida Safety Supply", "Carida"), ("Garel Composite Mills", "Garel"),
    ("Lothal Fleet Services", "Lothal"), ("Scarif Data Systems", "Scarif"), ("Chandrila Atmospherics", "Chandrila"),
    ("Mon Gazza Transport", "Mon Gazza"), ("Alsakan Instruments", "Alsakan"), ("Raxus Coolant Works", "Raxus"),
    ("Corellian Bulk Fasteners", "Corellia"),
]


@dataclass
class Supply:
    materials: list[dict]
    suppliers: list[dict]
    contracts: list[dict]
    purchase_orders: list[dict]
    po_lines: list[dict]
    inventory: list[dict]
    locations: list[dict]


def _slug(name: str) -> str:
    return "".join(ch for ch in name.lower().replace("&", "and") if ch.isalnum() or ch == " ").replace(" ", "-")


def _materials(rng) -> list[dict]:
    rows = []
    for index, (category, base, unit, low, high, strategic, hazardous, system, variants) in enumerate(MATERIAL_BASES, start=1):
        for v, variant in enumerate(variants, start=1):
            rows.append({
                "material_id": f"MAT-{index:03d}{v:02d}",
                "sku": f"EI-{system}-{index:03d}-{v:02d}",
                "name": f"{base}, {variant}",
                "category": category,
                "system_code": system,
                "unit": unit,
                "unit_cost_credits": round(rng.uniform(low, high), 2),
                "strategic": strategic,
                "hazardous": hazardous,
                "sensitivity": INTERNAL,
            })
    return rows


def _suppliers(rng) -> list[dict]:
    rows = []
    for index, (name, homeworld) in enumerate(SUPPLIERS, start=1):
        if name == KDY["name"]:
            first, last = KDY["account_manager"]
            domain = KDY["domain"]
        else:
            first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            domain = f"{_slug(name)}.example"
        rows.append({
            "supplier_id": f"SUP-{index:03d}",
            "name": name,
            "homeworld": homeworld,
            "contact_name": f"{first} {last}",
            "contact_email": f"{email_local_part(first, last)}@{domain}",
            "status": "ACTIVE" if rng.random() < 0.88 else rng.choice(("PROBATION", "SUSPENDED")),
            "performance_rating": round(rng.uniform(2.6, 4.9), 1),
            "sensitivity": INTERNAL,
        })
    rows[0]["status"] = "ACTIVE"
    return rows


def _contracts(rng, suppliers: list[dict], personnel: Personnel) -> list[dict]:
    legal = [e for e in personnel.active("LEG") if e.grade >= 6]
    rows = []
    counter = 0
    for supplier in suppliers:
        for _ in range(rng.choice((1, 1, 2))):
            counter += 1
            start = date(2021, 1, 4) + timedelta(days=rng.randint(0, 1500))
            rows.append({
                "contract_id": f"CTR-{start.year}-{counter + 200:04d}",
                "supplier_id": supplier["supplier_id"],
                "title": f"{supplier['name']} supply agreement {counter}",
                "start_date": start,
                "end_date": start + timedelta(days=rng.choice((365, 730, 1095))),
                "value_mcr": round(rng.uniform(40, 9000), 2),
                "owner_id": rng.choice(legal).employee_id,
                "status": "ACTIVE" if start + timedelta(days=365) > AS_OF else rng.choice(("ACTIVE", "EXPIRED")),
                "sensitivity": CONFIDENTIAL,
            })
    rows.insert(0, {
        "contract_id": KDY["contract_id"], "supplier_id": KDY["supplier_id"], "title": KDY["contract_title"],
        "start_date": KDY["contract_start"], "end_date": KDY["contract_end"], "value_mcr": KDY["contract_value_mcr"],
        "owner_id": personnel.by_handle["ashgrove"].employee_id, "status": "ACTIVE",
        "sensitivity": CONFIDENTIAL,
    })
    return rows


def _purchase_orders(rng, materials, suppliers, personnel: Personnel, programs: Programs):
    buyers = [e for e in personnel.active("SCM") if 4 <= e.grade <= 9]
    approvers = [e for e in personnel.active("SCM") if e.grade >= 10] + [personnel.by_handle["solberg"]]
    by_system: dict[str, list[dict]] = {}
    for material in materials:
        by_system.setdefault(material["system_code"], []).append(material)
    station_wps = [wp for wp in programs.work_packages if wp.program_id == canon.MAIN_PROGRAM and wp.start_date < AS_OF]
    orders, lines = [], []
    for n in range(1, 1451):
        wp = rng.choice(station_wps)
        pool = by_system.get(wp.system_code) or materials
        supplier = suppliers[0] if wp.system_code in KDY["systems"] and rng.random() < 0.35 else rng.choice(suppliers)
        order_date = wp.start_date + timedelta(days=rng.randint(0, max(1, (min(AS_OF, wp.end_date) - wp.start_date).days)))
        order_date = min(order_date, AS_OF)
        po_lines = []
        for line_no in range(1, rng.randint(1, 6) + 1):
            material = rng.choice(pool)
            qty = rng.choice((1, 2, 4, 6, 10, 12, 20, 40, 80, 120)) if material["unit_cost_credits"] < 50_000 else rng.choice((1, 1, 2, 3, 4))
            unit_price = round(material["unit_cost_credits"] * rng.uniform(0.95, 1.08), 2)
            po_lines.append({
                "po_id": f"PO-{n:06d}", "line_no": line_no, "material_id": material["material_id"],
                "quantity": qty, "unit_price_credits": unit_price,
                "line_total_credits": round(qty * unit_price, 2),
                "delivery_date": order_date + timedelta(days=rng.randint(14, 180)),
            })
        total = round(sum(line["line_total_credits"] for line in po_lines), 2)
        age = (AS_OF - order_date).days
        status = "RECEIVED" if age > 200 else rng.choice(("OPEN", "PARTIAL", "RECEIVED")) if age > 30 else "OPEN"
        if rng.random() < 0.03:
            status = "CANCELLED"
        orders.append({
            "po_id": f"PO-{n:06d}", "po_number": f"EI-PO-{order_date.year}-{n:05d}",
            "supplier_id": supplier["supplier_id"], "wp_id": wp.wp_id,
            "requested_by": rng.choice(buyers).employee_id,
            "approved_by": rng.choice(approvers).employee_id,
            "order_date": order_date, "status": status, "total_credits": total, "sensitivity": CONFIDENTIAL,
        })
        lines += po_lines
    return orders, lines


def _inventory(rng, materials) -> list[dict]:
    rows = []
    counter = 0
    for material in materials:
        for location in rng.sample(canon.LOCATIONS, rng.randint(1, 3)):
            counter += 1
            on_hand = rng.randint(0, 4000) if material["unit_cost_credits"] < 50_000 else rng.randint(0, 40)
            rows.append({
                "inventory_id": f"INV-{counter:05d}", "material_id": material["material_id"], "location_code": location[0],
                "quantity_on_hand": on_hand, "quantity_reserved": rng.randint(0, on_hand) if on_hand else 0,
                "last_counted": AS_OF - timedelta(days=rng.randint(1, 120)), "sensitivity": material["sensitivity"],
            })
    return rows


def build(personnel: Personnel, programs: Programs) -> Supply:
    rng = stream("supply")
    materials = _materials(rng)
    suppliers = _suppliers(rng)
    contracts = _contracts(rng, suppliers, personnel)
    orders, lines = _purchase_orders(rng, materials, suppliers, personnel, programs)
    locations = [{"location_code": code, "name": name, "location_type": kind, "planet": planet} for code, name, kind, planet in canon.LOCATIONS]
    return Supply(materials, suppliers, contracts, orders, lines, _inventory(rng, materials), locations)
