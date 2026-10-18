"""Messy files: what a real company share also holds.

- image-only scans with no text layer (a signed contract amendment, delivery notes, an invoice)
- a multi-sheet workbook with merged cells, formulas and a hidden, outdated sheet
- the 200+ page master system specification
- empty files, corrupt files, files with the wrong extension, legacy encodings,
  duplicates and awkward file names

Every item is recorded in the manifest under the ``messy`` category.
"""

import io
import zipfile
from datetime import date, timedelta

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from generator import canon
from generator.config import AS_OF
from generator.context import Context
from generator.docs.common import ENVIRONMENT_ROWS, GENERIC_REQUIREMENTS
from generator.docs.model import APPROVED, DRAFT, Doc, ScannedPages, Sheet
from generator.docs.render import ZIP_DATE, render
from generator.docs.technical import MASTER_SPEC, TEST_PLAN, WORKMANSHIP, icds_for
from generator.labels import CONFIDENTIAL, INTERNAL
from generator.supply import KDY

SCAN_SIZE = (1240, 1754)  # A4 at 150 dpi
MASTER_REVISION = "F"


def _plant(ctx: Context, item_id: str, kind: str, doc: Doc, description: str, expected_behavior: str, **extra) -> dict:
    source = ctx.truth.doc_source(doc, **extra)
    ctx.truth.plant(item_id=item_id, category="messy", title=f"{kind}: {doc.key}", description=description,
                    sensitivity=doc.true_sensitivity, locations=[source], expected_behavior=expected_behavior, kind=kind)
    return source


# --------------------------------------------------------------------------
# Scans
# --------------------------------------------------------------------------

def _scan_page(rng, lines: list[str]) -> bytes:
    """Render text like a photocopy: grey paper, speckles, a slight skew and blur, saved as a JPEG."""
    page = Image.new("L", SCAN_SIZE, 236)
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default(size=30)
    y = 140
    for line in lines:
        draw.text((120, y), line, font=font, fill=rng.randint(20, 50))
        y += 52 if line else 30
    for _ in range(1500):
        x, yy = rng.randrange(SCAN_SIZE[0]), rng.randrange(SCAN_SIZE[1])
        draw.point((x, yy), fill=rng.randint(60, 160))
    page = page.rotate(rng.uniform(-1.2, 1.2), resample=Image.Resampling.BILINEAR, fillcolor=236)
    page = page.filter(ImageFilter.GaussianBlur(0.7))
    buffer = io.BytesIO()
    page.save(buffer, format="JPEG", quality=55, optimize=False)
    return buffer.getvalue()


def _scan(ctx: Context, item_id: str, name: str, lines: list[str], **doc_fields) -> tuple[Doc, dict]:
    rng = ctx.rng(f"messy:scan:{name}")
    doc = ctx.store.add(Doc(fmt="pdf", content=ScannedPages([_scan_page(rng, lines)]), **doc_fields))
    source = _plant(ctx, item_id, "scanned", doc, "Image-only PDF: the text exists only as pixels; there is no text layer.",
                    "Read it with OCR; do not report the document as empty.", requires_ocr=True, ocr_text=" ".join(lines))
    return doc, source


def _scans(ctx: Context) -> None:
    contract = next(c for c in ctx.supply.contracts if c["contract_id"] == KDY["contract_id"])
    ashgrove = ctx.person("ashgrove")
    lines = [
        "AMENDMENT No. 2", "",
        f"to Contract {contract['contract_id']}: {contract['title']}",
        f"between {canon.COMPANY} and {KDY['name']}", "",
        f"1. The end date of the contract is moved from {contract['end_date'].isoformat()} to 2027-06-30.",
        f"2. The contract value of {contract['value_mcr']:,.2f} Mcr is unchanged.",
        "3. Gantry crane hoist deliveries are re-sequenced to follow slipway 2 completion.",
        "4. All other terms remain in force.", "",
        "Signed on 2026-08-14", "",
        f"For {canon.COMPANY}: {ashgrove.name}, {ashgrove.title}",
        f"For {KDY['name']}: Aurelia Vantress, Chief Executive Officer",
    ]
    _, source = _scan(ctx, "MSY-001", "kdy-amendment", lines, doc_number=f"{contract['contract_id']}-A2", title=f"Amendment No. 2 to {contract['contract_id']} (signed scan)",
                      doc_type="CONTRACT", key=f"legal/contracts/scans/{contract['contract_id']}_amendment-2_signed.pdf", label=CONFIDENTIAL,
                      created_date=date(2026, 8, 14), author_id=ashgrove.employee_id, author_name=ashgrove.name)
    ctx.truth.offer_question(
        pool="messy:scan-amendment", category="lookup", asked_as="analyst.confidential",
        question=f"After amendment No. 2, when does contract {contract['contract_id']} with Kuat Drive Yards end?",
        answer="2027-06-30", sources=[source, ctx.truth.row_source("contracts", CONFIDENTIAL, contract_id=contract["contract_id"])],
        notes="The contracts table still shows the original end date; the signed amendment scan moves it.",
    )

    kdy_po = next(p for p in ctx.supply.purchase_orders if p["supplier_id"] == KDY["supplier_id"] and p["status"] == "RECEIVED")
    po_lines = [line for line in ctx.supply.po_lines if line["po_id"] == kdy_po["po_id"]]
    materials = {m["material_id"]: m for m in ctx.supply.materials}
    lines = [f"{KDY['name']} - DELIVERY NOTE DN-{kdy_po['po_number'][-5:]}", "", f"Customer: {canon.COMPANY}, Starhaven Receiving Bay R-4",
             f"Your order: {kdy_po['po_number']}", f"Delivered: {(kdy_po['order_date'] + timedelta(days=40)).isoformat()}", ""]
    lines += [f"{line['line_no']}. {materials[line['material_id']]['name']} - {line['quantity']} {materials[line['material_id']]['unit']}" for line in po_lines]
    lines += ["", "Received in good condition. Signature: ______________"]
    _, source = _scan(ctx, "MSY-002", "kdy-delivery-note", lines, doc_number=f"DN-{kdy_po['po_number'][-5:]}", title=f"Delivery note for {kdy_po['po_number']} (scan)",
                      doc_type="DELIVERY_NOTE", key=f"procurement/delivery-notes/DN-{kdy_po['po_number'][-5:]}_scan.pdf", label=INTERNAL,
                      created_date=kdy_po["order_date"] + timedelta(days=40))
    first = po_lines[0]
    ctx.truth.offer_question(
        pool="messy:scan-delivery", category="lookup",
        question=f"According to the scanned delivery note for {kdy_po['po_number']}, how many units of line 1 were delivered?",
        answer=f"{first['quantity']} {materials[first['material_id']]['unit']}", must_include=[f"{first['quantity']} {materials[first['material_id']]['unit']}"],
        sources=[source],
    )

    steel = next(s for s in ctx.supply.suppliers if s["name"] == "Eriadu Steelworks")
    steel_po = next(p for p in ctx.supply.purchase_orders if p["supplier_id"] == steel["supplier_id"])
    delivered = steel_po["order_date"] + timedelta(days=21)
    lines = ["Eriadu Steelworks - LIEFERSCHEIN", "", f"Empfänger: {canon.GERMAN_SITE_DE}, Tor 3", f"Ihre Bestellung: {steel_po['po_number']}",
             f"Lieferdatum: {delivered:%d.%m.%Y}", "", "Pos. 1  Quadanium-Stahlträger 120 m  -  36 Stück", "Pos. 2  Schweißzusatz, Paket  -  80 Stück", "",
             "Ware ohne Beanstandung übernommen.", "Unterschrift Wareneingang: ______________"]
    _, source = _scan(ctx, "MSY-003", "eriadu-lieferschein", lines, doc_number=f"LS-{steel_po['po_number'][-5:]}", title=f"Lieferschein {steel_po['po_number']} (Scan)",
                      doc_type="DELIVERY_NOTE", key=f"procurement/delivery-notes/eriadu/Lieferschein_{steel_po['po_number']}.pdf", label=INTERNAL,
                      language="de", created_date=delivered)
    ctx.truth.offer_question(
        pool="messy:scan-lieferschein", category="lookup",
        question=f"How many quadanium steel beams does the scanned Eriadu delivery note for {steel_po['po_number']} list?",
        answer="36", must_include=["36 Stück"], sources=[source],
    )

    vendor = next(s for s in ctx.supply.suppliers if s["name"] == "Chandrila Atmospherics")
    vendor_po = next(p for p in ctx.supply.purchase_orders if p["supplier_id"] == vendor["supplier_id"])
    invoice = f"CA-INV-{vendor_po['po_number'][-5:]}"
    lines = [f"Chandrila Atmospherics - INVOICE {invoice}", "", f"Bill to: {canon.COMPANY}, Accounts Payable, {canon.HQ}",
             f"Purchase order: {vendor_po['po_number']}", f"Invoice date: {(vendor_po['order_date'] + timedelta(days=30)).isoformat()}", "",
             f"Amount due: {vendor_po['total_credits']:,.2f} credits", "Payment terms: 45 days net", "", "Thank you for your business."]
    _, source = _scan(ctx, "MSY-004", "chandrila-invoice", lines, doc_number=invoice, title=f"Invoice {invoice} (scan)", doc_type="INVOICE",
                      key=f"finance/invoices/scans/{invoice}.pdf", label=CONFIDENTIAL, created_date=vendor_po["order_date"] + timedelta(days=30))
    ctx.truth.offer_question(
        pool="messy:scan-invoice", category="cross_source", asked_as="analyst.confidential",
        question=f"Does the amount on scanned invoice {invoice} match the total of purchase order {vendor_po['po_number']}?",
        answer=f"Yes: {vendor_po['total_credits']:,.2f} credits", must_include=[f"{vendor_po['total_credits']:,.2f}"],
        sources=[source, ctx.truth.row_source("purchase_orders", CONFIDENTIAL, po_id=vendor_po["po_id"])],
    )


# --------------------------------------------------------------------------
# A multi-sheet workbook
# --------------------------------------------------------------------------

def _cost_model(ctx: Context) -> None:
    varga = ctx.person("varga")
    by_system = [["System", "Name", "Budget (Mcr)", "Actual (Mcr)", "Estimate to complete (Mcr)"]]
    # Data rows start at row 4: the renderer writes a banner row and a blank row above the header.
    for n, (code, spec) in enumerate(canon.SYSTEMS.items(), start=4):
        wps = ctx.programs.wps_for(code)
        by_system.append([code, spec["name"], round(sum(w.budget_mcr for w in wps), 2), round(sum(w.actual_mcr for w in wps), 2), f"=C{n}-D{n}"])
    progress = {row["zone_code"]: row["percent_complete"] for row in ctx.telemetry.progress if row["progress_date"] == AS_OF}
    by_zone = [["Zone", "Percent complete", "Remaining %"]] + [[zone, progress[zone], f"=100-B{n}"] for n, (zone, _) in enumerate(canon.ZONES, start=4)]
    doc = ctx.store.add(Doc(
        doc_number="FIN-MOD-SHV-CTC-07", title=f"{canon.STATION} cost-to-complete model v7", doc_type="FINANCIAL_MODEL", fmt="xlsx",
        key="finance/models/Starhaven_cost-to-complete_v7.xlsx", label=CONFIDENTIAL, created_date=date(2026, 9, 18), revision="7",
        author_id=varga.employee_id, author_name=varga.name,
        content=[
            Sheet("README", [["How to use this model"], ["Inputs drive every other sheet. Old_v1 is kept for reference only and is out of date."],
                             ["Owner", varga.name]], merges=("A3:E3", "A4:E4")),
            Sheet("Inputs", [["Parameter", "Base", "Low", "High"], ["Contingency", "8.5%", "5.0%", "12.0%"], ["Cost escalation per year", "3.2%", "2.0%", "4.5%"],
                             ["Labour productivity factor", "0.94", "0.90", "1.00"]], column_widths=(30, 10, 10, 10)),
            Sheet("By system", by_system, column_widths=(8, 36, 16, 16, 26)),
            Sheet("By zone", by_zone, column_widths=(8, 18, 14)),
            Sheet("Scenarios", [["Scenario", "Contingency", "Completion"], ["Base", "8.5%", "2027-06-30"], ["Low", "5.0%", "2027-05-14"], ["High", "12.0%", "2027-09-30"]]),
            Sheet("Old_v1", [["Parameter", "Value"], ["Contingency", "6.0%"], ["Completion", "2027-12-31"]], hidden=True),
        ],
    ))
    source = _plant(ctx, "MSY-005", "multi_sheet", doc, "Six sheets with merged cells, formulas without cached values and a hidden, outdated sheet (Old_v1).",
                    "Read the visible Inputs/Scenarios sheets; do not take values from the hidden Old_v1 sheet.")
    ctx.truth.offer_question(pool="messy:cost-model", category="lookup", asked_as="analyst.confidential",
                             question=f"What contingency does the base scenario of the {canon.STATION} cost-to-complete model v7 assume?",
                             answer="8.5%", sources=[source], must_not_include=["6.0%"], notes="Old_v1 (hidden) still shows 6.0%.")


# --------------------------------------------------------------------------
# The master system specification (200+ pages)
# --------------------------------------------------------------------------

def _zone_allocation(ctx: Context) -> dict[str, list[str]]:
    rng = ctx.rng("messy:zones")
    zones = [code for code, _ in canon.ZONES]
    return {c.code: sorted(rng.sample(zones, rng.randint(2, 6))) for c in ctx.engineering.components}


def _master_spec(ctx: Context) -> None:
    kalvane, tarrow = ctx.person("kalvane"), ctx.person("tarrow")
    allocation = _zone_allocation(ctx)
    blocks = [
        ("h1", "1. Introduction"),
        ("p", f"This specification is the top-level requirements document for {canon.STATION_LONG}. Each chapter covers one station system; "
              "each section covers one component, its requirements, its interfaces and its zone allocation."),
        ("table", ["System", "Name", "Lead department", "Components"],
         [[code, spec["name"], canon.DEPT_NAME[spec["dept"]], str(len(spec["components"]))] for code, spec in canon.SYSTEMS.items()]),
        ("pagebreak",),
    ]
    for chapter, (code, spec) in enumerate(canon.SYSTEMS.items(), start=2):
        blocks += [("h1", f"{chapter}. {spec['name']} ({code})"), ("p", spec["summary"]),
                   ("table", ["Document", "Title"], [list(icd) for icd in icds_for(code)] or [["-", "No external interfaces"]]), ("pagebreak",)]
        for section, comp in enumerate(ctx.engineering.for_system(code), start=1):
            rows = [[p.req_id, p.name, p.formatted(), f"±{p.tolerance_pct:g}%" if p.tolerance_pct else "exact", p.verification] for p in comp.params]
            installation = [[zone, f"Step {n} of {len(allocation[comp.code])}", "Construction Operations", "Quality Assurance & Test hold point"]
                            for n, zone in enumerate(allocation[comp.code], start=1)]
            documents = [[comp.spec_number, f"Rev {comp.spec_revision}", "Component specification"], [comp.drawing_number, "current", "General arrangement drawing"],
                         [comp.bom_number, "current", "Bill of materials"], [TEST_PLAN[0], "current", TEST_PLAN[1]], [WORKMANSHIP[0], "current", WORKMANSHIP[1]]]
            blocks += [
                ("h2", f"{chapter}.{section} {comp.name} ({comp.code})"),
                ("p", f"Detailed requirements: {comp.spec_number} Rev {comp.spec_revision}. Drawing: {comp.drawing_number}. Bill of materials: {comp.bom_number}."),
                ("table", ["Requirement", "Parameter", "Value", "Tolerance", "Verification"], rows),
                ("h3", "Verification approach"),
                ("bullets", [f"{p.req_id}: {p.verification.lower()} per the station verification and test plan." for p in comp.params]),
                ("pagebreak",),
                ("h3", f"{chapter}.{section}.1 Zone allocation and installation"),
                ("p", f"The {comp.name.lower()} is installed in zones {', '.join(allocation[comp.code])}."),
                ("table", ["Zone", "Sequence", "Installed by", "Inspection"], installation),
                ("h3", f"{chapter}.{section}.2 Environmental conditions"),
                ("table", ["Condition", "Value"], ENVIRONMENT_ROWS),
                ("pagebreak",),
                ("h3", f"{chapter}.{section}.3 Applicable documents"),
                ("table", ["Document", "Revision", "Title"], documents),
                ("h3", f"{chapter}.{section}.4 General requirements"),
                ("table", ["ID", "Requirement"], [[f"{comp.code}-G{n:02d}", f"{title}: {text}"] for n, (title, text) in enumerate(GENERIC_REQUIREMENTS, start=1)]),
                ("pagebreak",),
            ]
    matrix = [[c.code, c.name] + ["X" if zone in allocation[c.code] else "" for zone, _ in canon.ZONES[:12]] for c in ctx.engineering.components]
    blocks += [("h1", "Appendix A. Zone allocation matrix, northern hemisphere"), ("table", ["Component", "Name"] + [z for z, _ in canon.ZONES[:12]], matrix), ("pagebreak",)]
    matrix = [[c.code, c.name] + ["X" if zone in allocation[c.code] else "" for zone, _ in canon.ZONES[12:]] for c in ctx.engineering.components]
    blocks += [("h1", "Appendix B. Zone allocation matrix, southern hemisphere"), ("table", ["Component", "Name"] + [z for z, _ in canon.ZONES[12:]], matrix), ("pagebreak",)]
    blocks += [("h1", "Appendix C. Requirement index")]
    for comp in ctx.engineering.components:
        blocks.append(("table", ["Requirement", "Component", "Specification", "Value"], [[p.req_id, comp.name, comp.spec_number, p.formatted()] for p in comp.params]))
    doc = ctx.store.add(Doc(
        doc_number=MASTER_SPEC[0], title=MASTER_SPEC[1], doc_type="SPECIFICATION", fmt="pdf",
        key=f"engineering/specifications/{MASTER_SPEC[0]}_rev{MASTER_REVISION}.pdf", label=INTERNAL, created_date=date(2026, 4, 20),
        revision=MASTER_REVISION, approval_status=APPROVED, program_id=canon.MAIN_PROGRAM, author_id=kalvane.employee_id, author_name=kalvane.name,
        approver_id=tarrow.employee_id, approver_name=tarrow.name, approved_date=date(2026, 4, 20), content=blocks,
    ))
    source = _plant(ctx, "MSY-006", "long_document", doc, "The master system specification runs to more than 200 pages.",
                    "Find the specific section; answers deep in the document must cite it.")
    rng = ctx.rng("messy:master-spec-questions")
    for comp in rng.sample(ctx.engineering.components, 12):
        ctx.truth.offer_question(pool="messy:master-spec-zones", category="lookup",
                                 question=f"According to the master system specification {MASTER_SPEC[0]}, in which zones is the {comp.name.lower()} ({comp.code}) installed?",
                                 answer=", ".join(allocation[comp.code]), must_include=allocation[comp.code], sources=[source])


# --------------------------------------------------------------------------
# Empty, corrupt, mis-named and duplicate files
# --------------------------------------------------------------------------

def _raw(ctx: Context, item_id: str, kind: str, content: bytes, description: str, expected_behavior: str, **doc_fields) -> dict:
    doc = ctx.store.add(Doc(content=content, **doc_fields))
    return _plant(ctx, item_id, kind, doc, description, expected_behavior)


def _broken_xlsx() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        entry = zipfile.ZipInfo("[Content_Types].xml", date_time=ZIP_DATE)
        archive.writestr(entry, '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
    return buffer.getvalue()


def _empty_and_corrupt(ctx: Context) -> None:
    rng = ctx.rng("messy:corrupt")
    sallow = ctx.person("sallow")
    owner = {"author_id": sallow.employee_id, "author_name": sallow.name}
    source = _raw(ctx, "MSY-007", "empty", b"", "A zero-byte Markdown file.", "Say the file is empty; do not invent content.",
                  doc_number="PMO-NOTE-DRAFT", title="Notes draft", doc_type="NOTE", fmt="md", key="program-management/shared/notes_draft.md",
                  label=INTERNAL, approval_status=DRAFT, created_date=date(2026, 9, 3), **owner)
    ctx.truth.offer_question(pool="messy:empty", category="no_answer", question="What does the notes draft in program-management/shared/notes_draft.md say?",
                             answer=None, expected_type="not_found", sources=[source], notes="The file is empty (0 bytes).")
    _raw(ctx, "MSY-008", "empty", b"", "A zero-byte CSV export.", "Say the export is empty.",
         doc_number="SCM-EXP-EMPTY", title="Open orders export", doc_type="DATA_EXPORT", fmt="csv", key="procurement/exports/open_orders_export.csv",
         label=INTERNAL, created_date=date(2026, 9, 29), **owner)
    sample = ctx.store.docs[0]
    truncated = render(Doc(doc_number="QAT-RPT-2026-17", title="Quarterly quality summary Q2 2026", doc_type="REPORT", fmt="pdf", key="-", label=INTERNAL,
                           created_date=date(2026, 7, 8), company=canon.COMPANY,
                           content=[("h1", "Summary"), ("p", f"Quality summary for Q2 2026; see {sample.doc_number} for the first test report of the period.")] * 6))
    source = _raw(ctx, "MSY-009", "corrupt", truncated[: len(truncated) * 2 // 5], "A PDF cut off at 40% of its length (no cross-reference table, no trailer).",
                  "Report the file as unreadable; do not guess its content.",
                  doc_number="QAT-RPT-2026-17", title="Quarterly quality summary Q2 2026", doc_type="REPORT", fmt="pdf",
                  key="quality/reports/QAT-RPT-2026-17_quarterly-quality-summary.pdf", label=INTERNAL, created_date=date(2026, 7, 8))
    ctx.truth.offer_question(pool="messy:corrupt", category="no_answer", question="What are the conclusions of quality report QAT-RPT-2026-17?",
                             answer=None, expected_type="not_found", sources=[source], notes="The only copy is a truncated, unreadable PDF.")
    _raw(ctx, "MSY-010", "corrupt", rng.randbytes(6144), "Random bytes saved with a .docx extension.", "Report the file as unreadable.",
         doc_number="CON-MEMO-2026-22", title="Zone handover memo", doc_type="MEMO", fmt="docx", key="meetings/minutes/zone-handover/CON-MEMO-2026-22.docx",
         label=INTERNAL, created_date=date(2026, 6, 22))
    _raw(ctx, "MSY-011", "corrupt", _broken_xlsx(), "A ZIP container with only [Content_Types].xml: no workbook inside.", "Report the workbook as unreadable.",
         doc_number="FIN-WB-2026-31", title="Accruals workbook September", doc_type="WORKBOOK", fmt="xlsx", key="finance/workbooks/accruals_2026-09.xlsx",
         label=CONFIDENTIAL, created_date=date(2026, 9, 30))
    _raw(ctx, "MSY-012", "corrupt", b"\x89PNG\r\n\x1a\n" + rng.randbytes(2048), "A PNG signature followed by garbage.", "Report the image as unreadable.",
         doc_number="SHV-SF-PHOTO-0417", title="Site photo, zone 17 rib joint", doc_type="PHOTO", fmt="png", key="engineering/photos/Z17/rib-joint-0417.png",
         label=INTERNAL, created_date=date(2026, 5, 12))


def _wrong_formats(ctx: Context) -> None:
    hask = ctx.person("hask")
    text = "\n".join([
        "# Shuttle cradle maintenance checklist", "",
        "1. Inspect cradle clamps for wear every 200 docking cycles.",
        "2. Re-torque the cradle anchor bolts every 90 days.",
        "3. Replace the clamp pads at 1,500 cycles or when worn below 4 mm.", "",
        f"Owner: {hask.name}",
    ]) + "\n"
    source = _raw(ctx, "MSY-013", "wrong_extension", text.encode("utf-8"), "Plain Markdown text saved with a .pdf extension.",
                  "Read the content as text despite the extension.",
                  doc_number="HFO-CHK-0007", title="Shuttle cradle maintenance checklist", doc_type="CHECKLIST", fmt="pdf",
                  key="operations/checklists/shuttle-cradle-maintenance.pdf", label=INTERNAL, created_date=date(2026, 2, 9),
                  author_id=hask.employee_id, author_name=hask.name)
    ctx.truth.offer_question(pool="messy:wrong-extension", category="lookup",
                             question="According to the shuttle cradle maintenance checklist, after how many cycles must the clamp pads be replaced?",
                             answer="1,500 cycles", must_include=["1,500 cycles"], sources=[source])
    payload = '{"survey": "Tram ridership, band 6", "week": "2026-W36", "average_riders_per_hour": 842, "peak_hour": "07:00"}\n'
    _raw(ctx, "MSY-014", "wrong_extension", payload.encode("utf-8"), "JSON saved with a .csv extension.", "Parse the content as JSON.",
         doc_number="TR-SURVEY-2026-36", title="Tram ridership survey week 36", doc_type="SURVEY", fmt="csv", key="operations/surveys/tram-ridership-2026-w36.csv",
         label=INTERNAL, created_date=date(2026, 9, 7))


def _legacy_encoding(ctx: Context) -> None:
    brandt = ctx.person("brandt")
    materials = {m["material_id"]: m for m in ctx.supply.materials}
    stock = [row for row in ctx.supply.inventory if row["location_code"] == "LOC-ERI"]
    lines = ["Materialnummer;Bezeichnung;Menge;Einheit;Stückpreis (Credits);Zähldatum"]
    for row in stock:
        material = materials[row["material_id"]]
        price = f"{material['unit_cost_credits']:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
        lines.append(f"{material['material_id']};{material['name']};{row['quantity_on_hand']};{material['unit']};{price};{row['last_counted']:%d.%m.%Y}")
    content = ("\r\n".join(lines) + "\r\n").encode("cp1252", errors="replace")
    source = _raw(ctx, "MSY-015", "legacy_encoding", content, "Windows-1252 CSV with semicolons, decimal commas and German dates.",
                  "Decode as Windows-1252 and read the German number format correctly.",
                  doc_number="ERI-INV-2026-09", title="Inventurliste Fertigungswerft Eriadu", doc_type="INVENTORY_COUNT", fmt="csv",
                  key="operations/eriadu/Inventurliste_Eriadu_2026-09.csv", label=INTERNAL, language="de", created_date=date(2026, 9, 25),
                  author_id=brandt.employee_id, author_name=brandt.name)
    row = stock[0]
    ctx.truth.offer_question(pool="messy:legacy-encoding", category="lookup",
                             question=f"How many units of material {row['material_id']} were counted in the Eriadu inventory list (Inventurliste)?",
                             answer=str(row["quantity_on_hand"]), sources=[source, ctx.truth.row_source("inventory", INTERNAL, inventory_id=row["inventory_id"])])


def _duplicates_and_names(ctx: Context) -> None:
    approved = next(d for d in ctx.store.by_number("SHV-HA-SPEC-0003") if d.approval_status == APPROVED)
    copy = (ctx.store.root / approved.key).read_bytes()
    _raw(ctx, "MSY-016", "duplicate", copy, f"Byte-identical copy of {approved.document_id} ({approved.key}).",
         f"Treat as the same document as {approved.document_id}; do not count it twice.",
         doc_number=approved.doc_number, title=approved.title, doc_type=approved.doc_type, fmt=approved.fmt,
         key=f"engineering/specifications/HA/{approved.doc_number}_rev{approved.revision} (1).{approved.fmt}", label=approved.label, revision=approved.revision,
         created_date=approved.created_date)
    baseline = next(d for d in ctx.store.by_number(canon.SCHEDULE_BASELINE["doc_number"]) if d.approval_status == APPROVED)
    _raw(ctx, "MSY-017", "duplicate", (ctx.store.root / baseline.key).read_bytes(), f"Copy of {baseline.document_id} under an ad-hoc name.",
         f"Treat as the same document as {baseline.document_id}.",
         doc_number=baseline.doc_number, title=baseline.title, doc_type=baseline.doc_type, fmt=baseline.fmt,
         key="program-management/shared/IMS_baseline_FINAL_FINAL_v2.pdf", label=baseline.label, revision=baseline.revision, created_date=baseline.created_date)
    brandt = ctx.person("brandt")
    handover = Doc(
        doc_number="CON-UEB-Z17-E1", title="Übergabeprotokoll Zone 17 (Entwurf)", doc_type="HANDOVER", fmt="docx", label=INTERNAL, language="de",
        key="meetings/protokolle/Übergabeprotokoll Zone 17 – Entwurf.docx", approval_status=DRAFT, created_date=date(2026, 7, 2),
        author_id=brandt.employee_id, author_name=brandt.name,
        content=[("p", "Entwurf. Übergabe der Zone 17 an die Ausbaugewerke nach Wiederaufnahme der Arbeiten."),
                 ("table", ["Gewerk", "Übergabe geplant"], [["Ausbau Habitat", "14.09.2026"], ["Lebenserhaltung", "28.09.2026"]])],
    )
    ctx.store.add(handover)
    _plant(ctx, "MSY-018", "odd_name", handover, "Spaces, umlauts and an en dash in the object key.", "Handle the key exactly; do not mangle the name when citing it.")
    long_name = "starhaven-integration-working-group-" + "-".join(["notes"] * 30) + ".md"
    notes = Doc(doc_number="PMO-WG-NOTES-0031", title="Integration working group notes", doc_type="NOTE", fmt="md", label=INTERNAL,
                key=f"program-management/working-groups/{long_name}", created_date=date(2026, 6, 11),
                content=[("p", "Agreed: interface owners update open ICD items before every integration review.")])
    ctx.store.add(notes)
    _plant(ctx, "MSY-019", "odd_name", notes, f"An object key of {len(notes.key)} characters.", "Handle the long key exactly.")


def build(ctx: Context) -> None:
    _scans(ctx)
    _cost_model(ctx)
    _master_spec(ctx)
    _empty_and_corrupt(ctx)
    _wrong_formats(ctx)
    _legacy_encoding(ctx)
    _duplicates_and_names(ctx)
