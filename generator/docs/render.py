"""Turn a ``Doc`` into file bytes, one function per format.

Every renderer is deterministic: fixed timestamps in document metadata, fixed
ZIP entry dates for DOCX/XLSX, fixed MIME boundaries for email. The same input
always produces the same bytes.
"""

import csv
import email.policy
import io
import json
import re
import zipfile
from datetime import date
from email.message import EmailMessage
from xml.sax.saxutils import escape

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Font
from PIL import Image
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from generator.config import FIXED_TIMESTAMP
from generator.docs.model import Doc, ScannedPages, Sheet
from generator.labels import DISPLAY

rl_config.invariant = 1  # fixed CreationDate and document ID in every PDF

ZIP_DATE = (2026, 9, 30, 18, 0, 0)
ISO_FIXED = FIXED_TIMESTAMP.strftime("%Y-%m-%dT%H:%M:%SZ")

HEADER_FIELDS = {
    "en": ("Document number", "Revision", "Status", "Classification", "Author", "Approved by", "Date"),
    "de": ("Dokumentnummer", "Revision", "Status", "Einstufung", "Verfasser", "Freigegeben von", "Datum"),
}
STATUS_DE = {"APPROVED": "FREIGEGEBEN", "DRAFT": "ENTWURF", "IN_REVIEW": "IN PRÜFUNG", "SUPERSEDED": "ERSETZT", "REJECTED": "ABGELEHNT"}
BANNER_COLORS = {
    "PUBLIC": colors.HexColor("#2e7d32"),
    "INTERNAL": colors.HexColor("#1f4e8c"),
    "CONFIDENTIAL": colors.HexColor("#b26a00"),
    "RESTRICTED": colors.HexColor("#b71c1c"),
}

# Characters outside the PDF base-14 font encoding, mapped to safe equivalents.
PDF_SUBSTITUTIONS = str.maketrans({"≥": ">=", "≤": "<=", "→": "->", "ε": "e", "≈": "~", "×": "x"})


def banner(doc: Doc) -> str:
    return DISPLAY[doc.language][doc.label]


def _status(doc: Doc) -> str:
    return STATUS_DE.get(doc.approval_status, doc.approval_status) if doc.language == "de" else doc.approval_status


def header_rows(doc: Doc) -> list[tuple[str, str]]:
    names = HEADER_FIELDS[doc.language]
    when = doc.approved_date or doc.created_date
    values = (doc.doc_number, doc.revision, _status(doc), banner(doc), doc.author_name or doc.company, doc.approver_name or "-", when.isoformat())
    return list(zip(names, values))


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------

def _md_cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(doc: Doc) -> bytes:
    when = doc.approved_date or doc.created_date
    lines = [
        "---",
        f"document_number: {doc.doc_number}",
        f"title: \"{doc.title}\"",
        f"revision: \"{doc.revision}\"",
        f"status: {doc.approval_status}",
        f"classification: {doc.label}",
        f"author: \"{doc.author_name or doc.company}\"",
        f"approved_by: \"{doc.approver_name or ''}\"",
        f"date: {when.isoformat()}",
        f"language: {doc.language}",
        "---",
        "",
        f"**{banner(doc)}**",
        "",
        f"# {doc.title}",
        "",
        "| | |",
        "|---|---|",
    ]
    lines += [f"| {_md_cell(k)} | {_md_cell(v)} |" for k, v in header_rows(doc)]
    lines.append("")
    for block in doc.content:
        kind = block[0]
        if kind in ("h1", "h2", "h3"):
            lines += [f"{'#' * (int(kind[1]) + 1)} {block[1]}", ""]
        elif kind == "p":
            lines += [block[1], ""]
        elif kind == "bullets":
            lines += [f"- {item}" for item in block[1]] + [""]
        elif kind == "numbered":
            lines += [f"{n}. {item}" for n, item in enumerate(block[1], start=1)] + [""]
        elif kind == "table":
            headers, rows = block[1], block[2]
            lines.append("| " + " | ".join(_md_cell(h) for h in headers) + " |")
            lines.append("|" + "---|" * len(headers))
            lines += ["| " + " | ".join(_md_cell(c) for c in row) + " |" for row in rows]
            lines.append("")
        elif kind == "kv":
            lines += [f"- **{k}:** {v}" for k, v in block[1]] + [""]
        elif kind == "note":
            lines += [f"> {block[1]}", ""]
        elif kind == "hidden":
            lines += [f"<!-- {block[1]} -->", ""]
        elif kind == "pagebreak":
            lines += ["---", ""]
        else:
            raise ValueError(f"unknown block {kind}")
    lines += [f"**{banner(doc)}**", ""]
    return "\n".join(lines).encode("utf-8")


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------

_STYLES = getSampleStyleSheet()
_BODY = ParagraphStyle("Body", parent=_STYLES["BodyText"], fontName="Helvetica", fontSize=9.5, leading=12.5, spaceAfter=5)
_CELL = ParagraphStyle("Cell", parent=_BODY, fontSize=8, leading=10, spaceAfter=0)
_CELL_BOLD = ParagraphStyle("CellBold", parent=_CELL, fontName="Helvetica-Bold")
_NOTE = ParagraphStyle("Note", parent=_BODY, backColor=colors.HexColor("#f2f2f2"), borderPadding=5, leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=8)
_HIDDEN = ParagraphStyle("Hidden", parent=_BODY, fontSize=1, leading=1.2, textColor=colors.white, spaceAfter=0)
_HEADINGS = {
    "h1": ParagraphStyle("H1", parent=_STYLES["Heading1"], fontSize=14, spaceBefore=10, spaceAfter=6),
    "h2": ParagraphStyle("H2", parent=_STYLES["Heading2"], fontSize=11.5, spaceBefore=8, spaceAfter=4),
    "h3": ParagraphStyle("H3", parent=_STYLES["Heading3"], fontSize=10, spaceBefore=6, spaceAfter=3),
}
_TITLE = ParagraphStyle("DocTitle", parent=_STYLES["Title"], fontSize=17, spaceAfter=8)


def _pdf_text(value) -> str:
    return escape(str(value).translate(PDF_SUBSTITUTIONS))


def _pdf_table(headers, rows, widths=None) -> Table:
    data = [[Paragraph(_pdf_text(h), _CELL_BOLD) for h in headers]]
    data += [[Paragraph(_pdf_text(c), _CELL) for c in row] for row in rows]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e6e6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def _pdf_flowables(doc: Doc) -> list:
    flow = [Paragraph(_pdf_text(doc.title), _TITLE)]
    width = A4[0] - 36 * mm
    flow += [_pdf_table(["", ""], header_rows(doc), widths=[45 * mm, width - 45 * mm]), Spacer(1, 6 * mm)]
    for block in doc.content:
        kind = block[0]
        if kind in _HEADINGS:
            flow.append(Paragraph(_pdf_text(block[1]), _HEADINGS[kind]))
        elif kind == "p":
            flow.append(Paragraph(_pdf_text(block[1]), _BODY))
        elif kind in ("bullets", "numbered"):
            for n, item in enumerate(block[1], start=1):
                marker = "&bull;" if kind == "bullets" else f"{n}."
                flow.append(Paragraph(f"{marker} {_pdf_text(item)}", ParagraphStyle("Item", parent=_BODY, leftIndent=12, firstLineIndent=-8, spaceAfter=2)))
            flow.append(Spacer(1, 2 * mm))
        elif kind == "table":
            flow += [_pdf_table(block[1], block[2]), Spacer(1, 3 * mm)]
        elif kind == "kv":
            flow += [_pdf_table(["", ""], block[1], widths=[50 * mm, width - 50 * mm]), Spacer(1, 3 * mm)]
        elif kind == "note":
            flow.append(Paragraph(_pdf_text(block[1]), _NOTE))
        elif kind == "hidden":
            flow.append(Paragraph(_pdf_text(block[1]), _HIDDEN))
        elif kind == "pagebreak":
            flow.append(PageBreak())
        else:
            raise ValueError(f"unknown block {kind}")
    return flow


def render_pdf(doc: Doc) -> bytes:
    if isinstance(doc.content, ScannedPages):
        return render_scan(doc.content)
    buffer = io.BytesIO()
    label_text = banner(doc)
    color = BANNER_COLORS[doc.label]

    def decorate(canvas, template):
        canvas.saveState()
        width, height = A4
        canvas.setFillColor(color)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawCentredString(width / 2, height - 11 * mm, label_text)
        canvas.drawCentredString(width / 2, 8 * mm, label_text)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(18 * mm, 13 * mm, _pdf_text(f"{doc.company} | {doc.doc_number} Rev {doc.revision}"))
        canvas.drawRightString(width - 18 * mm, 13 * mm, f"{'Seite' if doc.language == 'de' else 'Page'} {canvas.getPageNumber()}")
        canvas.restoreState()

    template = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
        title=doc.title, author=doc.author_name or doc.company, subject=doc.doc_number, keywords=f"classification:{doc.label}",
        creator=doc.company, producer=doc.company,
    )
    template.build(_pdf_flowables(doc), onFirstPage=decorate, onLaterPages=decorate)
    return buffer.getvalue()


def render_scan(scan: ScannedPages) -> bytes:
    buffer = io.BytesIO()
    canvas = pdf_canvas.Canvas(buffer, pagesize=A4)
    canvas.setTitle("Scanned document")
    canvas.setCreator("Office copier")
    width, height = A4
    for page in scan.pages:
        canvas.drawImage(ImageReader(io.BytesIO(page)), 0, 0, width=width, height=height)
        canvas.showPage()
    canvas.save()
    return buffer.getvalue()


# --------------------------------------------------------------------------
# DOCX / XLSX
# --------------------------------------------------------------------------

def _normalize_ooxml(data: bytes) -> bytes:
    """Rewrite an OOXML ZIP with fixed entry dates and fixed core-property timestamps."""
    source = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            content = source.read(info.filename)
            if info.filename == "docProps/core.xml":
                content = re.sub(rb"(<dcterms:(created|modified)[^>]*>)[^<]*(</dcterms:\2>)", rb"\g<1>" + ISO_FIXED.encode() + rb"\3", content)
            entry = zipfile.ZipInfo(info.filename, date_time=ZIP_DATE)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            target.writestr(entry, content)
    return out.getvalue()


def _docx_banner(paragraph, text: str, rgb: str) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    run.bold = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor.from_string(rgb)


def _docx_table(document, headers, rows, header_row=True) -> None:
    table = document.add_table(rows=0, cols=len(headers))
    table.style = "Table Grid"
    if header_row:
        cells = table.add_row().cells
        for cell, value in zip(cells, headers):
            cell.text = ""
            cell.paragraphs[0].add_run(str(value)).bold = True
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = str(value)
    document.add_paragraph()


def render_docx(doc: Doc) -> bytes:
    document = DocxDocument()
    rgb = BANNER_COLORS[doc.label].hexval()[2:].upper()
    section = document.sections[0]
    _docx_banner(section.header.paragraphs[0], banner(doc), rgb)
    _docx_banner(section.footer.paragraphs[0], f"{banner(doc)}  |  {doc.doc_number} Rev {doc.revision}", rgb)
    document.add_heading(doc.title, 0)
    _docx_table(document, ["", ""], header_rows(doc), header_row=False)
    for block in doc.content:
        kind = block[0]
        if kind in ("h1", "h2", "h3"):
            document.add_heading(block[1], int(kind[1]))
        elif kind == "p":
            document.add_paragraph(block[1])
        elif kind == "bullets":
            for item in block[1]:
                document.add_paragraph(item, style="List Bullet")
        elif kind == "numbered":
            for item in block[1]:
                document.add_paragraph(item, style="List Number")
        elif kind == "table":
            _docx_table(document, block[1], block[2])
        elif kind == "kv":
            _docx_table(document, ["", ""], block[1], header_row=False)
        elif kind == "note":
            document.add_paragraph(block[1], style="Intense Quote")
        elif kind == "hidden":
            run = document.add_paragraph().add_run(block[1])
            run.font.hidden = True
            run.font.size = Pt(1)
        elif kind == "pagebreak":
            document.add_page_break()
        else:
            raise ValueError(f"unknown block {kind}")
    props = document.core_properties
    props.author = doc.author_name or doc.company
    props.last_modified_by = doc.author_name or doc.company
    props.title = doc.title
    props.subject = doc.doc_number
    props.category = banner(doc)
    props.keywords = f"classification:{doc.label}"
    props.comments = ""
    props.revision = 1
    props.created = FIXED_TIMESTAMP.replace(tzinfo=None)
    props.modified = FIXED_TIMESTAMP.replace(tzinfo=None)
    props.last_printed = FIXED_TIMESTAMP.replace(tzinfo=None)
    buffer = io.BytesIO()
    document.save(buffer)
    return _normalize_ooxml(buffer.getvalue())


def render_xlsx(doc: Doc) -> bytes:
    workbook = Workbook()
    workbook.remove(workbook.active)
    sheet: Sheet
    for sheet in doc.content:
        ws = workbook.create_sheet(sheet.name)
        ws.append([f"{banner(doc)} | {doc.doc_number} Rev {doc.revision} | {doc.title}"])
        ws["A1"].font = Font(bold=True, color=BANNER_COLORS[doc.label].hexval()[2:].upper())
        ws.append([])
        for n, row in enumerate(sheet.rows):
            ws.append(list(row))
            if n == 0:
                for cell in ws[ws.max_row]:
                    cell.font = Font(bold=True)
        for merge in sheet.merges:
            ws.merge_cells(merge)
        for index, width in enumerate(sheet.column_widths, start=1):
            ws.column_dimensions[ws.cell(row=1, column=index).column_letter].width = width
        if sheet.hidden:
            ws.sheet_state = "hidden"
    props = workbook.properties
    props.creator = doc.author_name or doc.company
    props.lastModifiedBy = doc.author_name or doc.company
    props.title = doc.title
    props.subject = doc.doc_number
    props.category = banner(doc)
    props.keywords = f"classification:{doc.label}"
    props.created = FIXED_TIMESTAMP.replace(tzinfo=None)
    props.modified = FIXED_TIMESTAMP.replace(tzinfo=None)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return _normalize_ooxml(buffer.getvalue())


# --------------------------------------------------------------------------
# Plain formats
# --------------------------------------------------------------------------

def render_csv(doc: Doc) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(doc.content)
    return buffer.getvalue().encode("utf-8")


def _json_default(value):
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"not JSON serializable: {type(value)}")


def render_json(doc: Doc) -> bytes:
    return (json.dumps(doc.content, indent=2, ensure_ascii=False, default=_json_default) + "\n").encode("utf-8")


def render_png(doc: Doc) -> bytes:
    image: Image.Image = doc.content
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def render_eml(doc: Doc) -> bytes:
    message: EmailMessage = doc.content
    return message.as_bytes(policy=email.policy.SMTP)


def render_text(doc: Doc) -> bytes:
    return doc.content.encode("utf-8")


def render_raw(doc: Doc) -> bytes:
    return doc.content


RENDERERS = {
    "md": render_markdown,
    "pdf": render_pdf,
    "docx": render_docx,
    "xlsx": render_xlsx,
    "csv": render_csv,
    "json": render_json,
    "svg": render_text,
    "ics": render_text,
    "png": render_png,
    "eml": render_eml,
}


def render(doc: Doc) -> bytes:
    if isinstance(doc.content, (bytes, bytearray)):
        return render_raw(doc)
    return RENDERERS[doc.fmt](doc)
