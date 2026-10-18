"""Engineering documents: specifications, design descriptions, interface control documents,
drawings, bills of materials, test reports, inspections, non-conformance reports and simulations.

Every value a document states comes from the engineering registry or the
structured data, so the ground-truth questions offered here can be answered
from the document alone or joined with a table.
"""

from datetime import date, timedelta
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

from generator import canon
from generator.config import AS_OF
from generator.context import Context
from generator.docs.common import ENVIRONMENT_ROWS, GENERIC_REQUIREMENTS, credits, pick
from generator.docs.model import APPROVED, Block, Doc, Sheet
from generator.engineering import Component, Parameter
from generator.labels import CONFIDENTIAL, DISPLAY, INTERNAL, RANK
from generator.personnel import Employee

MASTER_SPEC = ("SHV-SYS-SPEC-0001", f"{canon.STATION} Master System Specification")
TEST_PLAN = ("SHV-QA-PLN-0004", f"{canon.STATION} Verification and Test Plan")
WORKMANSHIP = ("SHV-QA-STD-0002", "Station Workmanship Standard")

ICD_PAIRS = [
    ("HR", "TX"), ("HR", "PD"), ("HR", "CN"), ("SA", "PD"), ("PD", "LS"), ("PD", "HB"), ("PD", "SY"), ("PD", "PR"),
    ("PD", "AG"), ("PD", "TR"), ("PD", "RL"), ("HB", "SY"), ("HB", "CN"), ("CN", "CM"), ("CN", "OC"), ("CN", "TR"),
    ("LS", "HA"), ("LS", "WM"), ("LS", "AG"), ("SF", "HB"), ("SF", "SY"), ("SF", "TR"), ("HA", "AG"), ("RL", "CN"),
]

ERIADU_SYSTEMS = ("SF", "HB", "SY", "LS", "HA", "WM")
LOWER_IS_BETTER = ("error", "latency", "time", "drift", "defect", "limit", "interval", "band")

TEST_TYPES = [
    ("Acceptance", "Abnahmeprüfung"), ("Qualification", "Qualifikationsprüfung"), ("Thermal vacuum", "Thermalvakuumprüfung"),
    ("Vibration", "Schwingungsprüfung"), ("Endurance", "Dauerlaufprüfung"), ("Functional", "Funktionsprüfung"),
]
TEST_SITES = ["Station Integration Test Facility, Zone Z05", "Station Integration Test Facility, Zone Z18", "Kuat Orbital Depot acceptance bay", "Coruscant qualification laboratory", "Eadu campus test laboratory"]
TEST_EQUIPMENT = [
    ("Calibrated field probe set", "Kalibrierter Feldsondensatz"), ("Thermal vacuum chamber TV-3", "Thermalvakuumkammer TV-3"),
    ("Six-axis shaker table", "Sechsachsiger Schwingtisch"), ("Data acquisition rack DAQ-12", "Messdatenerfassung DAQ-12"),
    ("Precision metrology arm", "Präzisions-Messarm"), ("Containment field analyser", "Eindämmungsfeld-Analysator"),
    ("Spectral alignment rig", "Spektral-Justiervorrichtung"),
]
COUNT_UNITS = ("ea", "class", "craft", "persons")

FINDINGS = [
    ("Weld porosity", "Porosität in Schweißnaht", "Grind out and re-weld; repeat inspection.", "Ausschleifen und nachschweißen; Nachprüfung."),
    ("Plate misalignment at seam", "Versatz am Plattenstoß", "Re-shim and re-torque the seam.", "Neu unterlegen und Stoß nachziehen."),
    ("Missing fastener", "Fehlendes Befestigungselement", "Install fastener per drawing and record torque.", "Befestigungselement nach Zeichnung setzen, Anzugsmoment dokumentieren."),
    ("Sealant gap", "Dichtungsspalt", "Clean and re-apply sealant; leak check.", "Reinigen, neu abdichten, Dichtheitsprüfung."),
    ("Conduit chafing", "Scheuerstelle an Leitung", "Add protective sleeve and re-route.", "Schutzschlauch anbringen und Leitung neu verlegen."),
    ("Corrosion spot", "Korrosionsstelle", "Treat and re-coat the area.", "Stelle behandeln und neu beschichten."),
    ("Damaged insulation", "Beschädigte Isolierung", "Replace insulation segment.", "Isoliersegment ersetzen."),
    ("Incorrect torque", "Falsches Anzugsmoment", "Re-torque to drawing value.", "Auf Zeichnungswert nachziehen."),
]
SEVERITIES = [("Minor", "Gering", 70), ("Major", "Erheblich", 25), ("Critical", "Kritisch", 5)]
INSPECTION_TYPES = [
    ("Weld inspection", "Schweißnahtprüfung"), ("Hull plating fit-up inspection", "Passungsprüfung Außenhautplatten"),
    ("Fastener torque audit", "Anzugsmoment-Audit"), ("Conduit routing inspection", "Prüfung Leitungsverlegung"),
    ("Pressure seal inspection", "Prüfung Druckdichtungen"),
]

SIMULATIONS = {
    "TX": ("Heat rejection transient", ["reactor_output_pct", "heat_exchanger_outlet_k", "radiator_temperature_k"]),
    "SA": ("Solar array output over one orbit", ["sun_angle_deg", "array_output_gw", "battery_charge_pct"]),
    "HB": ("Docking bay throughput", ["ships_docked", "queue_length", "deck_crew_utilization_pct"]),
    "HR": ("Reactor load-follow", ["demand_pct", "output_pct", "containment_margin_pct"]),
    "SF": ("Structural load case", ["load_factor", "max_rib_strain", "deflection_m"]),
    "LS": ("Atmosphere balance", ["crew_count", "oxygen_pct", "co2_ppm"]),
    "PD": ("Substation fault cascade", ["time_s", "zones_affected", "load_shed_pct"]),
    "AG": ("Hydroponic crop cycle", ["day", "biomass_kg", "water_use_m3"]),
}


# --------------------------------------------------------------------------
# Specifications
# --------------------------------------------------------------------------

def _verb(param: Parameter) -> str:
    return "not exceed" if any(word in param.name.lower() for word in LOWER_IS_BETTER) else "provide"


def _format(param: Parameter, value: float) -> str:
    return f"{value:,.{param.decimals}f} {param.unit}".strip()


def _tolerance(param: Parameter) -> str:
    return f"±{param.tolerance_pct:g}%" if param.tolerance_pct else "exact"


def icds_for(system_code: str) -> list[tuple[str, str]]:
    return [(f"SHV-ICD-{a}-{b}", f"Interface Control Document: {canon.SYSTEMS[a]['name']} / {canon.SYSTEMS[b]['name']}") for a, b in ICD_PAIRS if system_code in (a, b)]


def _revision_history(ctx: Context, comp: Component, revision: str, final_date: date, notes: dict[str, str] | None = None) -> list[list[str]]:
    rng = ctx.rng(f"technical:revhist:{comp.code}")
    letters = [chr(c) for c in range(ord("A"), ord(revision) + 1)]
    rows = []
    for n, letter in enumerate(letters):
        when = final_date - timedelta(days=(len(letters) - 1 - n) * rng.randint(90, 240))
        text = (notes or {}).get(letter) or ("Initial release." if n == 0 else rng.choice(("Updated requirement values after design review.", "Incorporated interface changes.", "Clarified verification methods.", "Editorial corrections.")))
        rows.append([letter, when.isoformat(), text, ctx.name(comp.engineer_id)])
    return rows


def component_spec_blocks(ctx: Context, comp: Component, revision: str, spec_date: date,
                          values: dict[str, float] | None = None, notes: dict[str, str] | None = None) -> list[Block]:
    """The body of a component specification; ``values`` overrides parameter values by name."""
    values = values or {}
    wp = next((w for w in ctx.programs.work_packages if w.wp_id == comp.work_package_id), None)
    scope = (f"Fabrication and installation are performed under work package {wp.wp_id} (WBS {wp.wbs_code}), owned by {ctx.name(wp.owner_id)}."
             if wp else f"The component is covered by the {comp.system_name} design and analysis work package.")
    applicable = [list(MASTER_SPEC), [comp.drawing_number, f"{comp.name} general arrangement drawing"], [comp.bom_number, f"{comp.name} bill of materials"], list(TEST_PLAN), list(WORKMANSHIP)]
    applicable += [list(icd) for icd in icds_for(comp.system_code)]
    requirements = []
    for param in comp.params:
        value = values.get(param.name, param.value)
        requirements.append([param.req_id, f"The {comp.name.lower()} shall {_verb(param)} a {param.name.lower()} of {_format(param, value)}.", _format(param, value), _tolerance(param), param.verification])
    generic = [[f"{comp.code}-G{n:02d}", f"{title}: {text}", "Inspection" if n % 2 else "Analysis"] for n, (title, text) in enumerate(GENERIC_REQUIREMENTS, start=1)]
    supplier = next(s for s in ctx.supply.suppliers if s["supplier_id"] == comp.supplier_id)
    return [
        ("h1", "1. Purpose"),
        ("p", f"This specification defines the performance, interface and verification requirements for the {comp.name.lower()} ({comp.code}) of the {comp.system_name} on {canon.STATION_LONG}."),
        ("h1", "2. Scope"),
        ("p", scope),
        ("p", f"The prime supplier for flight hardware is {supplier['name']}. Responsible engineer: {ctx.name(comp.engineer_id)}."),
        ("h1", "3. Applicable documents"),
        ("table", ["Document", "Title"], applicable),
        ("h1", "4. Description"),
        ("p", canon.SYSTEMS[comp.system_code]["summary"]),
        ("p", f"The {comp.name.lower()} is delivered as a set of line-replaceable assemblies, integrated on station by Construction Operations and verified by Quality Assurance & Test."),
        ("h1", "5. Performance requirements"),
        ("table", ["ID", "Requirement", "Value", "Tolerance", "Verification"], requirements),
        ("h2", "5.1 General requirements"),
        ("table", ["ID", "Requirement", "Verification"], generic),
        ("h1", "6. Environmental conditions"),
        ("table", ["Condition", "Value"], ENVIRONMENT_ROWS),
        ("h1", "7. Verification"),
        ("p", f"Each requirement is verified by the method stated in section 5, following {TEST_PLAN[0]}. Acceptance test reports are filed under the {comp.system_code} test-report series."),
        ("h1", "8. Revision history"),
        ("table", ["Rev", "Date", "Description", "Author"], _revision_history(ctx, comp, revision, spec_date, notes)),
    ]


def _spec_docs(ctx: Context) -> None:
    rng = ctx.rng("technical:specs")
    for comp in ctx.engineering.components:
        if comp.planted_spec:
            continue
        fmt = pick(rng, {"pdf": 55, "md": 30, "docx": 15})
        doc = ctx.store.add(Doc(
            doc_number=comp.spec_number, title=f"{comp.name} Specification", doc_type="SPECIFICATION", fmt=fmt,
            key=f"engineering/specifications/{comp.system_code}/{comp.spec_number}_rev{comp.spec_revision}.{fmt}",
            label=comp.label, created_date=comp.spec_date, revision=comp.spec_revision, approval_status=APPROVED,
            system_code=comp.system_code, program_id=canon.MAIN_PROGRAM,
            author_id=comp.engineer_id, author_name=ctx.name(comp.engineer_id),
            approver_id=comp.approver_id, approver_name=ctx.name(comp.approver_id), approved_date=comp.spec_date,
            content=component_spec_blocks(ctx, comp, comp.spec_revision, comp.spec_date),
        ))
        param = comp.params[0]
        ctx.truth.offer_question(
            pool="technical:spec-value", category="lookup",
            question=f"According to {comp.spec_number}, what {param.name.lower()} must the {comp.name.lower()} {_verb(param)}?",
            answer=param.formatted(), sources=[ctx.truth.doc_source(doc)],
        )
        approver = ctx.employee(comp.approver_id)
        if approver.is_active:
            today = canon.DEPT_NAME[approver.department]
        else:
            today = f"no longer with the company ({approver.termination_reason}, {approver.termination_date.isoformat()})"
        ctx.truth.offer_question(
            pool="technical:spec-approver-dept", category="cross_source",
            question=f"Who approved {comp.spec_number} ({comp.name} Specification), and which department do they lead or work in today?",
            answer=f"{approver.name}; {today}",
            must_include=[approver.last_name, canon.DEPT_NAME[approver.department] if approver.is_active else approver.termination_reason],
            sources=[ctx.truth.doc_source(doc), ctx.truth.row_source("employees", INTERNAL, employee_id=approver.employee_id),
                     ctx.truth.row_source("departments", INTERNAL, department_id=canon.DEPT_ID[approver.department])],
        )
        if comp.work_package_id:
            wp = next(w for w in ctx.programs.work_packages if w.wp_id == comp.work_package_id)
            ctx.truth.offer_question(
                pool="technical:spec-wp-budget", category="cross_source",
                question=f"What is the budget of the work package named in {comp.spec_number}?",
                answer=f"{wp.budget_mcr:,.2f} Mcr", must_include=[wp.wp_id, str(wp.budget_mcr)],
                sources=[ctx.truth.doc_source(doc), ctx.truth.row_source("work_packages", wp.sensitivity, wp_id=wp.wp_id)],
            )


def _design_descriptions(ctx: Context) -> None:
    rng = ctx.rng("technical:sdd")
    for code, spec in canon.SYSTEMS.items():
        components = ctx.engineering.for_system(code)
        head = ctx.head_of(spec["dept"], date(2024, 6, 3))
        author = ctx.employee(components[0].engineer_id)
        issued = date(2024, 6, 3) + timedelta(days=rng.randint(0, 300))
        revision = rng.choice("BCD")
        rows = [[c.code, c.name, c.spec_number, c.drawing_number, c.bom_number] for c in components]
        wps = ctx.programs.wps_for(code)
        blocks = [
            ("h1", "1. System overview"),
            ("p", spec["summary"]),
            ("p", f"The system is led by {canon.DEPT_NAME[spec['dept']]}. It is delivered through {len(wps)} work packages with a combined budget of {sum(w.budget_mcr for w in wps):,.2f} Mcr."),
            ("h1", "2. Components"),
            ("table", ["Code", "Component", "Specification", "Drawing", "Bill of materials"], rows),
            ("h1", "3. Architecture"),
        ]
        for comp in components:
            key_param = comp.params[0]
            blocks.append(("h2", f"3.{components.index(comp) + 1} {comp.name}"))
            blocks.append(("p", f"The {comp.name.lower()} is specified in {comp.spec_number}. Its governing parameter is the {key_param.name.lower()}, set at {key_param.formatted()}. The responsible engineer is {ctx.name(comp.engineer_id)}."))
        blocks += [
            ("h1", "4. Interfaces"),
            ("table", ["Document", "Title"], [list(icd) for icd in icds_for(code)] or [["-", "No external interfaces"]]),
            ("h1", "5. Work packages"),
            ("table", ["Work package", "Name", "Owner", "Status", "Complete"], [[w.wp_id, w.name, ctx.name(w.owner_id), w.status, f"{w.percent_complete}%"] for w in wps]),
            ("h1", "6. Risks"),
            ("bullets", [f"Supply of {c.name.lower()} assemblies depends on a single supplier." for c in components[:2]] + ["Integration slots in the station schedule are shared with neighbouring zones."]),
        ]
        ctx.store.add(Doc(
            doc_number=f"SHV-{code}-SDD-0001", title=f"{spec['name']}: System Design Description", doc_type="DESIGN_DESCRIPTION", fmt="pdf",
            key=f"engineering/specifications/{code}/SHV-{code}-SDD-0001_rev{revision}.pdf", label=spec["label"],
            created_date=issued, revision=revision, system_code=code, program_id=canon.MAIN_PROGRAM,
            author_id=author.employee_id, author_name=author.name,
            approver_id=head.employee_id, approver_name=head.name, approved_date=issued, content=blocks,
        ))


def _icds(ctx: Context) -> None:
    rng = ctx.rng("technical:icd")
    kinds = ["Mechanical", "Electrical power", "Data", "Thermal", "Grounding"]
    for a, b in ICD_PAIRS:
        number = f"SHV-ICD-{a}-{b}"
        side_a, side_b = canon.SYSTEMS[a], canon.SYSTEMS[b]
        owner = rng.choice([e for e in ctx.personnel.active("PMO") if 6 <= e.grade <= 11])
        issued = date(2023, 2, 6) + timedelta(days=rng.randint(0, 900))
        rows = []
        for n, kind in enumerate(rng.sample(kinds, rng.randint(3, 5)), start=1):
            rows.append([f"IF-{a}{b}-{n:02d}", kind, f"{side_a['name']} provides; {side_b['name']} receives", rng.choice(("Agreed", "Agreed", "Agreed", "Open"))])
        open_items = [r[0] for r in rows if r[3] == "Open"]
        label = max(side_a["label"], side_b["label"], key=RANK.get)
        fmt = "pdf" if rng.random() < 0.7 else "md"
        ctx.store.add(Doc(
            doc_number=number, title=f"Interface Control Document: {side_a['name']} / {side_b['name']}", doc_type="INTERFACE_CONTROL", fmt=fmt,
            key=f"engineering/icd/{number}.{fmt}", label=label, created_date=issued, revision=rng.choice("ABC"),
            system_code=a, program_id=canon.MAIN_PROGRAM, author_id=owner.employee_id, author_name=owner.name,
            approver_id=ctx.person("kalvane").employee_id, approver_name=ctx.person("kalvane").name, approved_date=issued,
            content=[
                ("h1", "1. Purpose"),
                ("p", f"This document controls the interfaces between the {side_a['name']} ({a}) and the {side_b['name']} ({b}). Changes require approval by the Chief Engineer, Station Integration."),
                ("h1", "2. Interfaces"),
                ("table", ["Interface", "Type", "Responsibility", "Status"], rows),
                ("h1", "3. Open items"),
                ("bullets", [f"{item}: values to be confirmed at the next integration review." for item in open_items] or ["None."]),
            ],
        ))


# --------------------------------------------------------------------------
# Drawings
# --------------------------------------------------------------------------

def _svg_text(x, y, text, size=14, anchor="start", weight="normal", fill="#d6e6ff") -> str:
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}">{escape(str(text))}</text>'


def _svg_figure(comp: Component) -> list[str]:
    name = comp.name.lower()
    stroke = 'fill="none" stroke="#9cc3ff" stroke-width="2"'
    cx, cy = 470, 400
    if any(word in name for word in ("telescope", "core", "vessel", "generator", "gyroscope", "dish", "processor")):
        shapes = [f'<circle cx="{cx}" cy="{cy}" r="{r}" {stroke}/>' for r in (210, 160, 110, 60)]
        shapes += [f'<line x1="{cx - 230}" y1="{cy}" x2="{cx + 230}" y2="{cy}" stroke="#5f8fd6" stroke-dasharray="8 6"/>',
                   f'<line x1="{cx}" y1="{cy - 230}" x2="{cx}" y2="{cy + 230}" stroke="#5f8fd6" stroke-dasharray="8 6"/>']
    elif any(word in name for word in ("shaft", "conduit", "ring", "loop", "manifold", "port", "track", "slipway", "dock")):
        shapes = [f'<rect x="{cx - 330}" y="{cy - 60}" width="660" height="120" {stroke}/>',
                  f'<rect x="{cx - 300}" y="{cy - 30}" width="600" height="60" {stroke}/>']
        shapes += [f'<line x1="{x}" y1="{cy - 60}" x2="{x}" y2="{cy + 60}" stroke="#5f8fd6"/>' for x in range(cx - 300, cx + 301, 100)]
    elif any(word in name for word in ("cradle", "bay", "quarters", "hall", "array", "string", "tier", "laboratory", "suite")):
        shapes = [f'<rect x="{cx - 300 + col * 120}" y="{cy - 180 + row * 120}" width="100" height="100" {stroke}/>' for row in range(3) for col in range(5)]
    else:
        shapes = [f'<rect x="{cx - 220}" y="{cy - 150}" width="440" height="300" rx="12" {stroke}/>',
                  f'<rect x="{cx - 180}" y="{cy - 110}" width="160" height="90" {stroke}/>',
                  f'<rect x="{cx + 20}" y="{cy - 110}" width="160" height="90" {stroke}/>',
                  f'<rect x="{cx - 180}" y="{cy + 10}" width="360" height="100" {stroke}/>']
    return shapes


def _svg_drawing(ctx: Context, comp: Component, drawn: Employee, checker: Employee, revision: str, issued: date) -> str:
    banner = DISPLAY["en"][comp.label]
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1189 841" width="1189" height="841" font-family="Helvetica, Arial, sans-serif">',
        f'<title>{escape(comp.drawing_number)} {escape(comp.name)} general arrangement</title>',
        '<rect x="0" y="0" width="1189" height="841" fill="#0b1e3a"/>',
        '<rect x="20" y="20" width="1149" height="801" fill="none" stroke="#cfe3ff" stroke-width="2"/>',
        _svg_text(594, 44, banner, 18, "middle", "bold", "#ff8a80"),
        _svg_text(594, 812, banner, 18, "middle", "bold", "#ff8a80"),
        _svg_text(40, 80, "NOTES", 15, weight="bold"),
        _svg_text(40, 102, "1. All dimensions in metres unless noted."),
        _svg_text(40, 122, f"2. Requirements per {comp.spec_number}."),
        _svg_text(40, 142, f"3. Materials per {comp.bom_number}."),
        _svg_text(40, 162, f"4. Workmanship per {WORKMANSHIP[0]}."),
    ]
    out += _svg_figure(comp)
    for n, param in enumerate(comp.params):
        y = 640 + n * 24
        out.append(_svg_text(60, y, f"{param.req_id}  {param.name}: {param.formatted()}", 15))
    for n, (number, _title) in enumerate(icds_for(comp.system_code)[:5]):
        y = 230 + n * 60
        out.append(f'<rect x="830" y="{y}" width="300" height="40" fill="none" stroke="#7fb0f5"/>')
        out.append(_svg_text(840, y + 25, f"IF {number}", 13))
        out.append(f'<line x1="690" y1="{y + 20}" x2="830" y2="{y + 20}" stroke="#7fb0f5" marker-end="none"/>')
    rows = [
        ("EMPIRE INCORPORATED", ""), ("TITLE", f"{comp.name} - general arrangement"), ("DRAWING NO.", comp.drawing_number),
        ("REV", revision), ("SCALE", "1:500"), ("DATE", issued.isoformat()), ("DRAWN", drawn.name),
        ("CHECKED", checker.name), ("APPROVED", ctx.name(comp.approver_id)), ("CLASSIFICATION", banner),
    ]
    out.append('<rect x="729" y="611" width="420" height="190" fill="#0b1e3a" stroke="#cfe3ff"/>')
    for n, (field, value) in enumerate(rows):
        y = 630 + n * 18
        out.append(_svg_text(739, y, field, 11, weight="bold"))
        out.append(_svg_text(869, y, value, 12))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _svg_drawings(ctx: Context) -> None:
    rng = ctx.rng("technical:svg")
    for comp in ctx.engineering.components:
        team = [e for e in ctx.personnel.active(canon.SYSTEMS[comp.system_code]["dept"]) if 4 <= e.grade <= 8]
        drawn, checker = rng.sample(team, 2)
        revision = rng.choice("ABBC")
        issued = comp.spec_date + timedelta(days=rng.randint(10, 120))
        ctx.store.add(Doc(
            doc_number=comp.drawing_number, title=f"{comp.name} general arrangement", doc_type="DRAWING", fmt="svg",
            key=f"engineering/drawings/{comp.system_code}/{comp.drawing_number}_rev{revision}.svg", label=comp.label,
            created_date=issued, revision=revision, system_code=comp.system_code, program_id=canon.MAIN_PROGRAM,
            author_id=drawn.employee_id, author_name=drawn.name, approver_id=comp.approver_id,
            approver_name=ctx.name(comp.approver_id), approved_date=issued,
            content=_svg_drawing(ctx, comp, drawn, checker, revision, issued),
        ))


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size=size)


def _png_frame(title: str, number: str, label: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1400, 900), (11, 30, 58))
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 1384, 884), outline=(207, 227, 255), width=2)
    banner = DISPLAY["en"][label]
    draw.text((700, 34), banner, font=_font(22), fill=(255, 138, 128), anchor="mm")
    draw.text((700, 866), banner, font=_font(22), fill=(255, 138, 128), anchor="mm")
    draw.text((40, 60), title, font=_font(26), fill=(214, 230, 255))
    draw.text((40, 96), f"{number}  |  Empire Incorporated", font=_font(18), fill=(160, 190, 230))
    return image, draw


def _system_diagram(ctx: Context, code: str) -> Image.Image:
    spec = canon.SYSTEMS[code]
    image, draw = _png_frame(f"{spec['name']}: block diagram", f"SHV-{code}-DWG-0100", spec["label"])
    components = ctx.engineering.for_system(code)
    draw.rectangle((560, 400, 840, 480), outline=(156, 195, 255), width=3)
    draw.text((700, 440), f"{code} system bus", font=_font(20), fill=(214, 230, 255), anchor="mm")
    for n, comp in enumerate(components):
        col, row = n % 4, n // 4
        x, y = 80 + col * 320, 170 + row * 470
        draw.rectangle((x, y, x + 260, y + 110), outline=(156, 195, 255), width=2)
        draw.text((x + 12, y + 14), comp.code, font=_font(18), fill=(255, 214, 140))
        draw.text((x + 12, y + 44), comp.name[:30], font=_font(16), fill=(214, 230, 255))
        draw.text((x + 12, y + 74), comp.params[0].formatted()[:30], font=_font(15), fill=(160, 190, 230))
        draw.line((x + 130, y + 110 if row == 0 else y, 700, 400 if row == 0 else 480), fill=(95, 143, 214), width=2)
    return image


def _zone_map(ctx: Context, zone: str, zone_name: str) -> Image.Image:
    image, draw = _png_frame(f"Station zone map: {zone_name}", f"SHV-SF-DWG-01{zone[1:]}", INTERNAL)
    cx, cy, r = 450, 480, 330
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(156, 195, 255), width=3)
    index = int(zone[1:])
    for band in range(1, 24):
        y = cy - r + band * (2 * r / 24)
        half = (r ** 2 - (y - cy) ** 2) ** 0.5
        color = (255, 214, 140) if band in (index - 1, index) else (60, 95, 150)
        draw.line((cx - half, y, cx + half, y), fill=color, width=4 if band in (index - 1, index) else 1)
    progress = [row for row in ctx.telemetry.progress if row["zone_code"] == zone][-1]
    sensors = [s["sensor_id"] for s in ctx.telemetry.sensors if s["zone_code"] == zone]
    lines = [f"Zone: {zone}", f"Construction complete: {progress['percent_complete']:.1f}% (as of {progress['progress_date']})", f"Crew on shift: {progress['crew_on_shift']}", "Sensors:"] + ([f"  {s}" for s in sensors] or ["  none"])
    for n, text in enumerate(lines):
        draw.text((860, 200 + n * 34), text, font=_font(20), fill=(214, 230, 255))
    return image


def _png_drawings(ctx: Context) -> None:
    kalvane = ctx.person("kalvane")
    for code, spec in canon.SYSTEMS.items():
        author = ctx.employee(ctx.engineering.for_system(code)[0].engineer_id)
        ctx.store.add(Doc(
            doc_number=f"SHV-{code}-DWG-0100", title=f"{spec['name']}: block diagram", doc_type="DRAWING", fmt="png",
            key=f"engineering/drawings/{code}/SHV-{code}-DWG-0100_block-diagram.png", label=spec["label"],
            created_date=date(2025, 2, 3), revision="A", system_code=code, program_id=canon.MAIN_PROGRAM,
            author_id=author.employee_id, author_name=author.name, approver_id=kalvane.employee_id,
            approver_name=kalvane.name, approved_date=date(2025, 2, 3), content=_system_diagram(ctx, code),
        ))
    for zone, zone_name in canon.ZONES:
        ctx.store.add(Doc(
            doc_number=f"SHV-SF-DWG-01{zone[1:]}", title=f"Station zone map: {zone_name}", doc_type="DRAWING", fmt="png",
            key=f"engineering/drawings/SF/zone-maps/{zone}.png", label=INTERNAL, created_date=AS_OF, revision="A",
            system_code="SF", program_id=canon.MAIN_PROGRAM, author_id=kalvane.employee_id, author_name=kalvane.name,
            content=_zone_map(ctx, zone, zone_name),
        ))


# --------------------------------------------------------------------------
# Bills of materials
# --------------------------------------------------------------------------

def _bom_lines(ctx: Context, comp: Component) -> list[list]:
    rng = ctx.rng(f"technical:bom:{comp.code}")
    pool = [m for m in ctx.supply.materials if m["system_code"] == comp.system_code] or ctx.supply.materials
    supplier_names = {s["supplier_id"]: s["name"] for s in ctx.supply.suppliers}
    lines = []
    for n in range(1, rng.randint(6, 15) + 1):
        material = rng.choice(pool)
        qty = rng.choice((1, 2, 4, 8, 12, 24, 48, 96, 240)) if material["unit_cost_credits"] < 50_000 else rng.choice((1, 2, 3, 4, 8))
        lines.append([n, material["sku"], material["name"], qty, material["unit"], f"{material['unit_cost_credits']:.2f}",
                      f"{qty * material['unit_cost_credits']:.2f}", supplier_names[comp.supplier_id if n == 1 else rng.choice(sorted(supplier_names))], comp.drawing_number])
    return lines


BOM_HEADER = ["line", "part_number", "description", "quantity", "unit", "unit_cost_credits", "extended_cost_credits", "supplier", "drawing"]


def _boms(ctx: Context) -> None:
    for code, spec in canon.SYSTEMS.items():
        components = ctx.engineering.for_system(code)
        all_lines, summary = [], [["component", "name", "bom", "lines", "total_cost_credits"]]
        for comp in components:
            lines = _bom_lines(ctx, comp)
            total = sum(float(line[6]) for line in lines)
            summary.append([comp.code, comp.name, comp.bom_number, len(lines), round(total, 2)])
            all_lines += [[comp.code] + line for line in lines]
            ctx.store.add(Doc(
                doc_number=comp.bom_number, title=f"{comp.name} bill of materials", doc_type="BILL_OF_MATERIALS", fmt="csv",
                key=f"engineering/bom/{code}/{comp.bom_number}.csv", label=CONFIDENTIAL,
                created_date=comp.spec_date, revision=comp.spec_revision, system_code=code, program_id=canon.MAIN_PROGRAM,
                author_id=comp.engineer_id, author_name=ctx.name(comp.engineer_id), content=[BOM_HEADER] + lines,
            ))
        suppliers = sorted({line[8] for line in all_lines})
        ctx.store.add(Doc(
            doc_number=f"SHV-{code}-BOM-0300", title=f"{spec['name']}: consolidated bill of materials", doc_type="BILL_OF_MATERIALS", fmt="xlsx",
            key=f"engineering/bom/{code}/SHV-{code}-BOM-0300_consolidated.xlsx", label=CONFIDENTIAL,
            created_date=date(2025, 9, 1), revision="C", system_code=code, program_id=canon.MAIN_PROGRAM,
            author_id=components[0].engineer_id, author_name=ctx.name(components[0].engineer_id),
            content=[
                Sheet("Summary", summary, column_widths=(12, 40, 22, 8, 20)),
                Sheet("Lines", [["component"] + BOM_HEADER] + all_lines, column_widths=(10, 6, 18, 44, 10, 6, 16, 18, 30, 20)),
                Sheet("Suppliers", [["supplier"]] + [[name] for name in suppliers], column_widths=(40,)),
            ],
        ))


# --------------------------------------------------------------------------
# Test reports and non-conformance reports
# --------------------------------------------------------------------------

def _measured_decimals(param: Parameter) -> int:
    return param.decimals if param.unit in COUNT_UNITS else param.decimals + 1


def _measure(rng, param: Parameter, force_fail: bool) -> tuple[float, bool]:
    if not param.tolerance_pct:
        return param.value, True
    spread = abs(param.value) * param.tolerance_pct / 100
    measured = param.value + rng.gauss(0, spread / 2.5)
    if force_fail:
        measured = param.value + spread * rng.choice((-1, 1)) * rng.uniform(1.2, 1.8)
    measured = round(measured, _measured_decimals(param))
    return measured, abs(measured - param.value) <= spread


class _NcrLog:
    """Collects non-conformances raised by tests and inspections; written out at the end."""

    def __init__(self):
        self.items: list[dict] = []

    def raise_ncr(self, raised: date, raised_by: Employee, subject: str, description: str, source_number: str, system: str | None, language: str) -> str:
        number = f"NCR-{raised.year}-{len(self.items) + 1:04d}"
        self.items.append({"number": number, "raised": raised, "raised_by": raised_by, "subject": subject, "description": description,
                           "source": source_number, "system": system, "language": language})
        return number


def _test_reports(ctx: Context, ncrs: _NcrLog) -> None:
    rng = ctx.rng("technical:tests")
    testers_en = [e for e in ctx.personnel.active("QAT") if e.language == "en" and e.grade <= 9]
    testers_de = [e for e in ctx.personnel.german_speakers() if e.department in ("QAT", "CON") and e.grade <= 9]
    counters: dict[str, int] = {}
    for _ in range(224):
        comp = rng.choice(ctx.engineering.components)
        german = comp.system_code in ERIADU_SYSTEMS and rng.random() < 0.42
        lang = "de" if german else "en"
        tester = rng.choice(testers_de if german else testers_en)
        test_en, test_de = rng.choice(TEST_TYPES)
        tested = date(2023, 6, 5) + timedelta(days=rng.randint(0, (AS_OF - date(2023, 6, 5)).days))
        counters[comp.system_code] = counters.get(comp.system_code, 0) + 1
        number = f"SHV-{comp.system_code}-TR-{counters[comp.system_code]:04d}"
        serial = f"SN-{comp.system_code}-{rng.randint(100, 9999):04d}"
        site = "Fertigungswerft Eriadu, Prüfhalle 2" if german else rng.choice(TEST_SITES)
        toleranced = [p for p in comp.params if p.tolerance_pct]
        fail_param = rng.choice(toleranced) if toleranced and rng.random() < 0.09 else None
        results, failed = [], []
        for param in comp.params:
            measured, ok = _measure(rng, param, param is fail_param)
            verdict = ("BESTANDEN" if ok else "NICHT BESTANDEN") if german else ("PASS" if ok else "FAIL")
            results.append([param.req_id, param.name, _format(param, param.value), _tolerance(param), f"{measured:,.{_measured_decimals(param)}f} {param.unit}".strip(), verdict])
            if not ok:
                failed.append((param, measured))
        overall = "FAIL" if failed else "PASS"
        ncr = None
        if failed:
            param, measured = failed[0]
            ncr = ncrs.raise_ncr(tested, tester, f"{comp.name} {serial}", f"{param.name} measured {measured:,.{_measured_decimals(param)}f} {param.unit}, outside {_tolerance(param)} of {_format(param, param.value)}.", number, comp.system_code, lang)
        witness = ctx.employee(comp.engineer_id)
        procedure = f"TP-{comp.code}-{rng.randint(1, 12):02d}"
        equipment = [pair[1] if german else pair[0] for pair in rng.sample(TEST_EQUIPMENT, 3)]
        if german:
            title = f"Prüfbericht {test_de}: {comp.name} ({serial})"
            blocks = [
                ("h1", "1. Prüfgegenstand"),
                ("kv", [("Bauteil", f"{comp.name} ({comp.code})"), ("Seriennummer", serial), ("Spezifikation", f"{comp.spec_number} Rev {comp.spec_revision}"), ("Prüfvorschrift", procedure)]),
                ("h1", "2. Prüfaufbau"),
                ("p", f"Die Prüfung wurde am {tested:%d.%m.%Y} in der {site} durchgeführt. Prüfer: {tester.name}. Zeuge: {witness.name}."),
                ("bullets", equipment),
                ("h1", "3. Ergebnisse"),
                ("table", ["Anforderung", "Parameter", "Sollwert", "Toleranz", "Messwert", "Ergebnis"], results),
                ("h1", "4. Abweichungen"),
                ("p", f"Abweichung festgestellt; Nichtkonformitätsbericht {ncr} eröffnet." if ncr else "Keine Abweichungen."),
                ("h1", "5. Bewertung"),
                ("p", "Die Prüfung ist NICHT BESTANDEN. Das Bauteil bleibt gesperrt bis zur Klärung." if ncr else "Die Prüfung ist BESTANDEN. Das Bauteil wird zur Integration freigegeben."),
            ]
        else:
            title = f"{test_en} test report: {comp.name} ({serial})"
            blocks = [
                ("h1", "1. Item under test"),
                ("kv", [("Component", f"{comp.name} ({comp.code})"), ("Serial number", serial), ("Specification", f"{comp.spec_number} Rev {comp.spec_revision}"), ("Procedure", procedure)]),
                ("h1", "2. Test set-up"),
                ("p", f"The test was performed on {tested.isoformat()} at the {site}. Test engineer: {tester.name}. Witness: {witness.name}."),
                ("bullets", equipment),
                ("h1", "3. Results"),
                ("table", ["Requirement", "Parameter", "Required", "Tolerance", "Measured", "Result"], results),
                ("h1", "4. Anomalies"),
                ("p", f"Out-of-tolerance result recorded; non-conformance report {ncr} raised." if ncr else "None."),
                ("h1", "5. Conclusion"),
                ("p", f"Overall result: {overall}. " + ("The unit is held pending disposition of the non-conformance." if ncr else "The unit is released for integration.")),
            ]
        fmt = pick(rng, {"pdf": 50, "md": 40, "docx": 10})
        doc = ctx.store.add(Doc(
            doc_number=number, title=title, doc_type="TEST_REPORT", fmt=fmt,
            key=f"engineering/test-reports/{comp.system_code}/{number}.{fmt}", label=comp.label, created_date=tested,
            system_code=comp.system_code, program_id=canon.MAIN_PROGRAM, author_id=tester.employee_id, author_name=tester.name,
            approver_id=witness.employee_id, approver_name=witness.name, approved_date=tested, language=lang, content=blocks,
        ))
        measured_param = next((p for p in comp.params if p.tolerance_pct), comp.params[0])
        row = next(r for r in results if r[0] == measured_param.req_id)
        ctx.truth.offer_question(
            pool="technical:test-measured", category="lookup",
            question=f"In test report {number}, what {measured_param.name.lower()} was measured on unit {serial}, and did it pass?",
            answer=f"{row[4]}; {row[5]}", must_include=[row[4], row[5]], sources=[ctx.truth.doc_source(doc)],
        )
        ctx.truth.offer_question(
            pool="technical:test-tester-dept", category="cross_source",
            question=f"Which department does the engineer who performed test {number} work in?",
            answer=canon.DEPT_NAME[tester.department], must_include=[canon.DEPT_NAME[tester.department]],
            sources=[ctx.truth.doc_source(doc), ctx.truth.row_source("employees", INTERNAL, employee_id=tester.employee_id),
                     ctx.truth.row_source("departments", INTERNAL, department_id=canon.DEPT_ID[tester.department])],
        )


def _inspections(ctx: Context, ncrs: _NcrLog) -> None:
    rng = ctx.rng("technical:inspections")
    inspectors_en = [e for e in ctx.personnel.active("QAT") + ctx.personnel.active("CON") if e.language == "en" and e.grade <= 9]
    inspectors_de = [e for e in ctx.personnel.german_speakers() if e.grade <= 9]
    zones = [code for code, _ in canon.ZONES]
    used: set[str] = set()
    for _ in range(162):
        german = rng.random() < 0.44
        lang = "de" if german else "en"
        inspector = rng.choice(inspectors_de if german else inspectors_en)
        when = date(2024, 1, 8) + timedelta(days=rng.randint(0, (AS_OF - date(2024, 1, 8)).days))
        where = "ERI" if german else rng.choice(zones)
        n = 1
        while f"INS-{where}-{when:%Y%m%d}-{n}" in used:
            n += 1
        number = f"INS-{where}-{when:%Y%m%d}-{n}"
        used.add(number)
        kind_en, kind_de = rng.choice(INSPECTION_TYPES)
        findings = []
        for f in range(1, rng.randint(2, 8) + 1):
            what_en, what_de, action_en, action_de = rng.choice(FINDINGS)
            sev_en, sev_de, _ = rng.choices(SEVERITIES, weights=[s[2] for s in SEVERITIES], k=1)[0]
            deck, frame = rng.randint(1, 84), rng.randint(1, 360)
            due = when + timedelta(days=rng.choice((3, 7, 14, 30)))
            if german:
                location = f"Modul {rng.choice('ABCDEFGH')}-{rng.randint(10, 99)}, Spant {frame}"
                findings.append([f"F-{f:02d}", what_de, location, sev_de, action_de, due.strftime("%d.%m.%Y")])
            else:
                findings.append([f"F-{f:02d}", what_en, f"Deck {deck}, frame {frame}", sev_en, action_en, due.isoformat()])
            if sev_en == "Critical":
                ncrs.raise_ncr(when, inspector, f"{number} {findings[-1][0]}", f"{findings[-1][1]} at {findings[-1][2]}.", number, "SF", lang)
        critical = sum(1 for f in findings if f[3] in ("Critical", "Kritisch"))
        if german:
            title = f"Prüfprotokoll {kind_de}, {canon.GERMAN_SITE_DE}, {when:%d.%m.%Y}"
            blocks = [
                ("kv", [("Prüfart", kind_de), ("Ort", canon.GERMAN_SITE_DE), ("Datum", when.strftime("%d.%m.%Y")), ("Prüfer", inspector.name), ("Anzahl Befunde", str(len(findings)))]),
                ("h1", "Befunde"),
                ("table", ["Nr.", "Befund", "Ort", "Schwere", "Maßnahme", "Frist"], findings),
                ("h1", "Bewertung"),
                ("p", f"{critical} kritische Befunde; Nichtkonformitätsberichte wurden eröffnet." if critical else "Keine kritischen Befunde. Freigabe nach Abarbeitung der Maßnahmen."),
            ]
        else:
            title = f"{kind_en}, {where}, {when.isoformat()}"
            blocks = [
                ("kv", [("Inspection type", kind_en), ("Zone", where), ("Date", when.isoformat()), ("Inspector", inspector.name), ("Number of findings", str(len(findings)))]),
                ("h1", "Findings"),
                ("table", ["ID", "Finding", "Location", "Severity", "Action", "Due"], findings),
                ("h1", "Assessment"),
                ("p", f"{critical} critical findings; non-conformance reports raised." if critical else "No critical findings. Release after the actions are closed."),
            ]
        fmt = "pdf" if rng.random() < 0.35 else "md"
        doc = ctx.store.add(Doc(
            doc_number=number, title=title, doc_type="INSPECTION_REPORT", fmt=fmt,
            key=f"engineering/inspections/{where}/{number}.{fmt}", label=INTERNAL if german or rng.random() < 0.6 else CONFIDENTIAL,
            created_date=when, system_code="SF", program_id=canon.MAIN_PROGRAM, author_id=inspector.employee_id,
            author_name=inspector.name, language=lang, content=blocks,
        ))
        ctx.truth.offer_question(
            pool="technical:inspection-count", category="lookup",
            question=f"How many findings were recorded in inspection report {number}?",
            answer=str(len(findings)), sources=[ctx.truth.doc_source(doc)],
        )


def _ncr_docs(ctx: Context, ncrs: _NcrLog) -> None:
    rng = ctx.rng("technical:ncr")
    approvers = [e for e in ctx.personnel.active("QAT") if e.grade >= 10]
    dispositions = [("Rework", "Nacharbeit"), ("Repair", "Reparatur"), ("Use as is", "Verwendung wie besehen"), ("Scrap", "Verschrottung")]
    for item in ncrs.items:
        approver = rng.choice(approvers)
        disp_en, disp_de = rng.choice(dispositions)
        cost = round(rng.uniform(4_000, 2_400_000), 2)
        closed = item["raised"] + timedelta(days=rng.randint(5, 90))
        status = "CLOSED" if closed <= AS_OF else "OPEN"
        if item["language"] == "de":
            blocks = [
                ("kv", [("NCR", item["number"]), ("Gegenstand", item["subject"]), ("Quelle", item["source"]), ("Eröffnet am", item["raised"].strftime("%d.%m.%Y")), ("Eröffnet von", item["raised_by"].name), ("Status", "GESCHLOSSEN" if status == "CLOSED" else "OFFEN")]),
                ("h1", "Beschreibung"), ("p", item["description"]),
                ("h1", "Entscheidung"), ("p", f"{disp_de}. Kostenauswirkung: {cost:,.2f} Credits. Freigabe durch {approver.name}."),
            ]
            title = f"Nichtkonformitätsbericht {item['number']}: {item['subject']}"
        else:
            blocks = [
                ("kv", [("NCR", item["number"]), ("Subject", item["subject"]), ("Source", item["source"]), ("Raised", item["raised"].isoformat()), ("Raised by", item["raised_by"].name), ("Status", status)]),
                ("h1", "Description"), ("p", item["description"]),
                ("h1", "Disposition"), ("p", f"{disp_en}. Cost impact: {credits(cost)}. Approved by {approver.name}."),
            ]
            title = f"Non-conformance report {item['number']}: {item['subject']}"
        ctx.store.add(Doc(
            doc_number=item["number"], title=title, doc_type="NONCONFORMANCE_REPORT", fmt="md",
            key=f"engineering/ncr/{item['raised'].year}/{item['number']}.md", label=CONFIDENTIAL, created_date=item["raised"],
            system_code=item["system"], program_id=canon.MAIN_PROGRAM, author_id=item["raised_by"].employee_id,
            author_name=item["raised_by"].name, approver_id=approver.employee_id, approver_name=approver.name,
            approved_date=closed if status == "CLOSED" else None, approval_status=APPROVED if status == "CLOSED" else "IN_REVIEW",
            language=item["language"], content=blocks,
        ))


# --------------------------------------------------------------------------
# Simulations
# --------------------------------------------------------------------------

def _simulations(ctx: Context) -> None:
    rng = ctx.rng("technical:simulations")
    systems = sorted(SIMULATIONS)
    for n in range(1, 53):
        code = systems[(n - 1) % len(systems)]
        title, columns = SIMULATIONS[code]
        engineer = rng.choice([e for e in ctx.personnel.active(canon.SYSTEMS[code]["dept"]) if 5 <= e.grade <= 9])
        run = date(2024, 3, 4) + timedelta(days=rng.randint(0, (AS_OF - date(2024, 3, 4)).days))
        steps = rng.randint(24, 48)
        base = [rng.uniform(10, 90) for _ in columns]
        series = []
        for step in range(steps):
            point = {"t": step}
            for column, value in zip(columns, base):
                point[column] = round(value * (1 + 0.15 * ((step / steps) - 0.5)) + rng.gauss(0, value * 0.02), 3)
            series.append(point)
        peak_column = columns[-1]
        peak = max(series, key=lambda p: p[peak_column])
        number = f"SHV-{code}-SIM-{n:04d}"
        doc = ctx.store.add(Doc(
            doc_number=number, title=f"{title} (run {n})", doc_type="SIMULATION", fmt="json",
            key=f"engineering/simulations/{code}/{number}.json", label=canon.SYSTEMS[code]["label"], created_date=run,
            system_code=code, program_id=canon.MAIN_PROGRAM, author_id=engineer.employee_id, author_name=engineer.name,
            content={
                "simulation_id": number, "title": f"{title} (run {n})", "system": code, "classification": canon.SYSTEMS[code]["label"],
                "model_version": f"{rng.randint(2, 6)}.{rng.randint(0, 9)}.{rng.randint(0, 20)}", "run_date": run, "engineer": engineer.name,
                "engineer_id": engineer.employee_id, "inputs": {"scenario": rng.choice(("nominal", "degraded", "peak demand", "contingency")), "duration_steps": steps},
                "results": {"summary": {f"peak_{peak_column}": peak[peak_column], "peak_step": peak["t"]}, "series": series},
            },
        ))
        ctx.truth.offer_question(
            pool="technical:simulation-peak", category="lookup",
            question=f"In simulation {number}, what was the peak {peak_column} and at which step did it occur?",
            answer=f"{peak[peak_column]} at step {peak['t']}", must_include=[str(peak[peak_column]), str(peak["t"])], sources=[ctx.truth.doc_source(doc)],
        )


def build(ctx: Context) -> None:
    ncrs = _NcrLog()
    _spec_docs(ctx)
    _design_descriptions(ctx)
    _icds(ctx)
    _svg_drawings(ctx)
    _png_drawings(ctx)
    _boms(ctx)
    _test_reports(ctx, ncrs)
    _inspections(ctx, ncrs)
    _ncr_docs(ctx, ncrs)
    _simulations(ctx)

