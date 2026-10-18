"""Communications: email, chat exports, helpdesk and facilities tickets, and calendar invites.

Messages talk about the work the structured data records (purchase orders,
work packages, leadership changes, non-conformance reports, the Zone Z17 beam
shortage, the reactor temperature peak of 12 September 2026) and take every
fact from the same record the database is loaded from, so the ground-truth
questions offered here can be answered from a message alone or joined with a
table.
"""

import csv
import io
import itertools
import textwrap
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from generator import canon
from generator.config import AS_OF, EMPIRE_DOMAIN, FIXED_TIMESTAMP
from generator.context import Context
from generator.docs.common import ERIADU_SKIP, REVIEW_SKIP, de_date, leader_row, leadership_source, progress_on
from generator.docs.mail import email_message, ics_fold, ics_text
from generator.docs.model import Doc
from generator.facilities import PEAK_INCIDENT, PLACES
from generator.labels import CONFIDENTIAL, DISPLAY, INTERNAL
from generator.personnel import Employee
from generator.supply import KDY
from generator.telemetry import FOLLOWER_PEAK, FOLLOWER_SENSOR, PEAK_AT, PEAK_SENSOR, PEAK_VALUE, STALL_END, STALL_START, STALLED_ZONE

WINDOW_START = date(2026, 1, 1)   # chat exports and calendar invites cover January to September 2026
TICKETS_START = date(2025, 1, 2)
EXPORTED_AT = FIXED_TIMESTAMP

CHANNELS = (
    # channel, language, first month
    ("starhaven-integration", "en", 1),
    ("reactor-ops", "en", 1),
    ("procurement", "en", 1),
    ("eriadu-werft", "de", 1),
    ("general", "en", 1),
    ("it-help", "en", 1),
    ("shipyard-planning", "en", 4),
)

IT_TOPICS = [
    ("Datapad screen cracked", "My datapad screen cracked after it fell off the desk.", "Replacement datapad issued."),
    ("Mailbox full", "I cannot receive mail because my mailbox is full.", "Mailbox quota raised and old items archived."),
    ("Holo-projector not working in meeting room {room}", "The holo-projector in meeting room {room} shows no image.", "Projector emitter replaced."),
    ("Printer on floor {floor} jams", "The printer on floor {floor} jams on every second page.", "Feed rollers cleaned and replaced."),
    ("Software install request: {tool}", "Please install the {tool} on my workstation.", "Installed and licensed."),
    ("Network slow at {place}", "The network has been very slow at {place} since this morning.", "Faulty switch port replaced."),
    ("Shared folder for {program}", "Please create a shared folder for the {program} team.", "Folder created and team members added."),
    ("Calendar not syncing on datapad", "My datapad calendar stopped syncing with the mail system.", "Sync profile reset."),
    ("New starter equipment", "A new colleague starts next week and needs a workstation and a datapad.", "Workstation and datapad prepared."),
]
FACILITY_TOPICS = [
    ("Lost badge replacement", "I lost my badge near {place}.", "Badge replaced at reception."),
    ("Coolant drip at {place}", "There is a slow coolant drip from a pipe joint at {place}.", "Joint resealed."),
    ("Light fixture flickering at {place}", "A light fixture at {place} keeps flickering.", "Fixture replaced."),
    ("Office chair broken", "The gas lift of my office chair is broken.", "Chair replaced."),
    ("Room too warm at {place}", "The temperature at {place} stays above 26 °C all afternoon.", "Thermostat recalibrated."),
    ("Cleaning request: {place}", "Please arrange an extra clean at {place} after the move.", "Cleaning completed."),
    ("Turbolift noise near {place}", "The turbolift near {place} makes a grinding noise.", "Guide rollers lubricated."),
]
IT_TOPICS_DE = [
    ("Drucker in Halle {hall} druckt nicht", "Der Drucker in Halle {hall} meldet einen Papierstau.", "Papierstau behoben."),
    ("Datapad startet nicht", "Mein Datapad startet seit heute Morgen nicht mehr.", "Akku getauscht."),
    ("Postfach voll", "Ich kann keine Mails mehr empfangen, das Postfach ist voll.", "Postfach erweitert und alte Mails archiviert."),
    ("Software für Messarm installieren", "Bitte die Auswertesoftware für den Messarm in Halle {hall} installieren.", "Software installiert."),
]
FACILITY_TOPICS_DE = [
    ("Beleuchtung in Halle {hall} flackert", "Die Hallenbeleuchtung in Halle {hall} flackert seit gestern.", "Leuchtmittel getauscht."),
    ("Kaffeemaschine im Pausenraum außer Betrieb", "Die Kaffeemaschine im Pausenraum von Halle {hall} funktioniert nicht.", "Maschine entkalkt und repariert."),
    ("Werksausweis verloren", "Ich habe meinen Werksausweis in Halle {hall} verloren.", "Neuer Ausweis ausgestellt."),
    ("Büro neben Halle {hall} zu warm", "Im Büro neben Halle {hall} ist es dauerhaft zu warm.", "Thermostat neu eingestellt."),
]
TICKET_TOPICS = {
    ("IT_HELPDESK", "en"): IT_TOPICS, ("FACILITIES", "en"): FACILITY_TOPICS,
    ("IT_HELPDESK", "de"): IT_TOPICS_DE, ("FACILITIES", "de"): FACILITY_TOPICS_DE,
}
ROOMS = ("OC-2", "H41-07", "H41-12", "LAB-B3", "ERI-1-04")
TOOLS = ("structural analysis suite", "schedule planner", "drawing viewer", "statistics package", "thermal model toolkit")

MAINTENANCE_SERVICES = ("mail system", "document registry", "planning system", "HoloNet relay", "shared drives", "service desk portal")
DELAY_REASONS = ("tooling change at our plant", "change of transport slot", "late raw material delivery to our mill")
FAREWELL_REASONS = {
    "Resigned": ("I am leaving to take up a new role elsewhere.", "Ich wechsle zu einem neuen Arbeitgeber."),
    "Retired": ("I am retiring after {years} years with the company.", "Ich gehe nach {years} Jahren in den Ruhestand."),
    "Moved to a partner company": ("I am moving to one of our partner companies.", "Ich wechsle zu einem Partnerunternehmen."),
    "Relocated with family": ("I am relocating with my family.", "Ich ziehe mit meiner Familie um."),
}
UNITS_DE = {"ea": "Stück", "set": "Sätze", "kit": "Kits", "pack": "Packungen"}


# --------------------------------------------------------------------------
# Participants, lookups and text helpers
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Party:
    """Someone who sends or receives messages: an employee, a supplier contact or a distribution list."""

    name: str
    email: str
    employee_id: str | None = None
    signature: str = ""

    @property
    def address(self) -> str:
        return f"{self.name} <{self.email}>"

    @property
    def first(self) -> str:
        return self.name.split()[0]


ALL_STAFF = Party("All Staff", f"all-staff@{EMPIRE_DOMAIN}")
PROGRAM_LIST = Party(f"{canon.STATION} Program", f"starhaven-program@{EMPIRE_DOMAIN}")
ERIADU_TEAM = Party("Team Fertigungswerft Eriadu", f"eriadu-team@{EMPIRE_DOMAIN}")
REACTOR_OPS = Party("Reactor Operations", f"reactor-ops@{EMPIRE_DOMAIN}")
SERVICE_DESK = Party("Service Desk Team", f"service-desk@{EMPIRE_DOMAIN}")


def _party(employee: Employee) -> Party:
    site = f"{canon.COMPANY}, {canon.GERMAN_SITE_DE}" if employee.language == "de" else canon.COMPANY
    signature = f"{employee.name}\n{employee.title}\n{canon.DEPT_NAME[employee.department]}\n{site}\nExt. {employee.comm_extension}"
    return Party(employee.name, employee.email, employee.employee_id, signature)


def _supplier_party(supplier: dict) -> Party:
    role = "Key Account Manager" if supplier["supplier_id"] == KDY["supplier_id"] else "Customer Service"
    return Party(supplier["contact_name"], supplier["contact_email"], signature=f"{supplier['contact_name']}\n{role}\n{supplier['name']}")


def _people(employees: list[Employee], low: int, high: int, language: str | None = None) -> list[Employee]:
    """Generated (not hand-built) employees within a grade range, optionally of one language."""
    return [e for e in employees if low <= e.grade <= high and e.handle is None and (language is None or e.language == language)]


@dataclass
class _Index:
    """Lookups over the structured data that several builders share."""

    suppliers: dict[str, dict]
    materials: dict[str, dict]
    po_lines: dict[str, list[dict]]
    progress: dict[tuple[date, str], float]


def _index(ctx: Context) -> _Index:
    po_lines: dict[str, list[dict]] = {}
    for line in ctx.supply.po_lines:
        po_lines.setdefault(line["po_id"], []).append(line)
    return _Index(
        suppliers={s["supplier_id"]: s for s in ctx.supply.suppliers},
        materials={m["material_id"]: m for m in ctx.supply.materials},
        po_lines=po_lines,
        progress={(row["progress_date"], row["zone_code"]): row["percent_complete"] for row in ctx.telemetry.progress},
    )


def _successions(terms: list[tuple[str, str, date]]) -> list[tuple[str, str, str, date]]:
    """(entity, outgoing handle, incoming handle, effective date) for consecutive terms of the same entity."""
    by_entity: dict[str, list[tuple[str, date]]] = {}
    for entity, handle, start in terms:
        by_entity.setdefault(entity, []).append((handle, start))
    return [(entity, old, new, start) for entity, rows in by_entity.items() for (old, _), (new, start) in itertools.pairwise(rows)]


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=timezone.utc)


def _weekday(day: date) -> date:
    """The day itself, or the following Monday if it falls on a weekend."""
    return day + timedelta(days=7 - day.weekday()) if day.weekday() >= 5 else day


def _office(rng, day: date) -> datetime:
    return _at(_weekday(day), rng.randint(8, 17), rng.randrange(60))


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _fill(text: str, indent: str = "") -> str:
    return "\n".join(textwrap.fill(line, 72, subsequent_indent=indent, break_long_words=False, break_on_hyphens=False) if line else ""
                     for line in text.splitlines())


def _body(*blocks: str | list[str]) -> str:
    """Paragraphs separated by blank lines; a list becomes a bullet list. Lines wrap at 72 characters."""
    return "\n\n".join("\n".join(_fill(f"- {item}", "  ") for item in block) if isinstance(block, list) else _fill(block) for block in blocks)


def _csv(rows: list[list]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


# --------------------------------------------------------------------------
# Mail
# --------------------------------------------------------------------------

@dataclass
class Mail:
    """A message already written to the store, kept so replies can quote and reference it."""

    doc: Doc
    message_id: str
    references: tuple[str, ...]
    sender: Party
    sent: datetime
    text: str


def _quote(parent: Mail, language: str) -> str:
    if language == "de":
        intro = f"Am {de_date(parent.sent.date())} um {parent.sent:%H:%M} schrieb {parent.sender.name}:"
    else:
        intro = f"On {parent.sent:%Y-%m-%d} at {parent.sent:%H:%M} UTC, {parent.sender.name} wrote:"
    return "\n".join([intro] + [f"> {line}" if line else ">" for line in parent.text.splitlines()])


@dataclass
class _Mailer:
    """Writes messages as .eml documents, numbering them and chaining replies."""

    ctx: Context
    sent: list[Mail] = field(default_factory=list)

    def send(self, sender: Party, to: list[Party], sent: datetime, subject: str, body: str, label: str = INTERNAL,
             language: str = "en", cc: list[Party] = (), parent: Mail | None = None,
             attachment: tuple[str, str] | None = None) -> Mail:
        number = len(self.sent) + 1
        local = f"{sent:%Y%m%d%H%M}.{number:05d}"
        text = body + (f"\n\n-- \n{sender.signature}" if sender.signature else "")
        if parent:
            text += "\n\n" + _quote(parent, language)
        message = email_message(sender.email, sender.name, [p.address for p in to], subject, sent,
                                f"{DISPLAY[language][label]}\n\n{text}\n", local, label)
        if cc:
            message["Cc"] = ", ".join(p.address for p in cc)
        references = ()
        if parent:
            references = parent.references + (parent.message_id,)
            message["In-Reply-To"] = parent.message_id
            message["References"] = " ".join(references)
        if attachment:
            filename, content = attachment
            message.add_attachment(content, subtype="csv", filename=filename)
            message.set_boundary(f"=_empire_mail_{number:05d}")
        doc = self.ctx.store.add(Doc(
            doc_number=local, title=subject, doc_type="EMAIL", fmt="eml", key=f"mail/{sent:%Y}/{sent:%m}/{local}.eml", label=label,
            created_date=sent.date(), author_id=sender.employee_id, author_name=sender.name,
            language=language, content=message,
        ))
        mail = Mail(doc, str(message["Message-ID"]), references, sender, sent, text)
        self.sent.append(mail)
        return mail

    def reply(self, parent: Mail, sender: Party, to: list[Party], sent: datetime, body: str, label: str | None = None) -> Mail:
        prefix = "AW: " if parent.doc.language == "de" else "Re: "
        subject = parent.doc.title if parent.doc.title.startswith(prefix) else prefix + parent.doc.title
        return self.send(sender, to, sent, subject, body, label or parent.doc.label, parent.doc.language, parent=parent)


def _offer_succession(ctx: Context, mail: Mail, pool: str, entity: tuple[str, str, str], start: date, question: str) -> None:
    """A temporal question before and after a leadership change, answered by the leadership table."""
    for day in (start - timedelta(days=20), start + timedelta(days=20)):
        row = leader_row(ctx, *entity, day)
        ctx.truth.offer_question(
            pool=pool, category="temporal", question=question.format(day=day.isoformat()), answer=ctx.name(row["employee_id"]),
            sources=[ctx.truth.doc_source(mail.doc), leadership_source(ctx, row)],
        )


def _announcements(ctx: Context, mailer: _Mailer) -> None:
    rng = ctx.rng("comms:announcements")
    chairman = _party(ctx.person("ashworth"))
    brandt = _party(ctx.person("brandt"))
    for dept, old_handle, new_handle, start in _successions([(dept, handle, start) for dept, handle, start, _ in canon.DEPARTMENT_HEADS]):
        old, new = ctx.person(old_handle), ctx.person(new_handle)
        name = canon.DEPT_NAME[dept]
        if old.is_active:
            leaving = f"{old.name} moves to the {canon.DEPT_NAME[old.department]} as {old.title}."
            leaving_de = f"{old.name} wechselt in die Abteilung {canon.DEPT_NAME[old.department]}."
        else:
            years = (old.termination_date - old.hire_date).days // 365
            leaving = f"{old.name} retires on {old.termination_date.isoformat()} after {years} years with {canon.COMPANY}."
            leaving_de = f"{old.name} geht zum {de_date(old.termination_date)} in den Ruhestand."
        sent = _office(rng, start - timedelta(days=14))
        mail = mailer.send(chairman, [ALL_STAFF], sent, f"Leadership change in {name}", _body(
            "Dear colleagues,",
            f"{leaving} From {start.isoformat()}, {new.name} leads {name} as {new.title}.",
            f"Please join me in thanking {old.first_name} and in welcoming {new.first_name} to the role.",
            f"Best regards,\n{chairman.first}",
        ))
        mailer.send(brandt, [ERIADU_TEAM], _office(rng, sent.date() + timedelta(days=1)), f"Personalmitteilung: neue Leitung {name}", _body(
            "Hallo zusammen,",
            f"zur Info aus der Unternehmensleitung: {leaving_de} Ab dem {de_date(start)} leitet {new.name} die Abteilung {name}.",
            f"Viele Grüße\n{brandt.first}",
        ), language="de")
        _offer_succession(ctx, mail, "comms:head-change", ("DEPARTMENT", canon.DEPT_ID[dept], "HEAD"), start, f"Who headed {name} on {{day}}?")

    directors = [(program, handle, start) for program, handle, role, start, _ in canon.PROGRAM_ROLES if role == "PROGRAM_DIRECTOR"]
    for program_id, old_handle, new_handle, start in _successions(directors):
        old, new = ctx.person(old_handle), ctx.person(new_handle)
        program = next(p for p in ctx.programs.programs if p["program_id"] == program_id)
        if old.is_active:
            reason = f"{old.first_name} will concentrate on leading {canon.DEPT_NAME[old.department]}."
        else:
            reason = f"{old.first_name} retires on {old.termination_date.isoformat()}."
        recipients = [PROGRAM_LIST] if program_id == canon.MAIN_PROGRAM else [ALL_STAFF]
        mail = mailer.send(chairman, recipients, _office(rng, start - timedelta(days=10)), f"New program director for {program['name']}", _body(
            "Dear colleagues,",
            f"From {start.isoformat()}, {new.name} takes over as program director of {program['name']} from {old.name}. {reason}",
            "Thank you all for your support during the handover.",
            f"Best regards,\n{chairman.first}",
        ))
        _offer_succession(ctx, mail, "comms:program-director-change", ("PROGRAM", program_id, "PROGRAM_DIRECTOR"), start,
                          f"Who was the program director of {program['name']} on {{day}}?")


# --------------------------------------------------------------------------
# Supplier correspondence
# --------------------------------------------------------------------------

def _kdy_mail(ctx: Context, mailer: _Mailer, index: _Index) -> None:
    rng = ctx.rng("comms:kdy")
    danvik = _supplier_party(index.suppliers[KDY["supplier_id"]])
    kdy_orders = [po for po in ctx.supply.purchase_orders if po["supplier_id"] == KDY["supplier_id"]]
    recent = [po for po in kdy_orders if po["status"] != "CANCELLED" and date(2024, 6, 1) <= po["order_date"] <= AS_OF - timedelta(days=10)]
    confirmations = []
    for po in sorted(rng.sample(recent, min(16, len(recent))), key=lambda p: p["po_id"]):
        lines = index.po_lines[po["po_id"]]
        first, last = min(line["delivery_date"] for line in lines), max(line["delivery_date"] for line in lines)
        buyer = _party(ctx.employee(po["requested_by"]))
        request = mailer.send(buyer, [danvik], _office(rng, po["order_date"] + timedelta(days=rng.randint(1, 4))), f"Delivery schedule for {po['po_number']}", _body(
            f"Hello {danvik.first},",
            f"could you confirm the delivery schedule for purchase order {po['po_number']}? It covers {len(lines)} line(s) for work package {po['wp_id']} under contract {KDY['contract_id']}.",
            f"Thanks,\n{buyer.first}",
        ))
        schedule = f"final delivery on {last.isoformat()}" if last != first else "all lines in one shipment"
        reply = mailer.reply(request, danvik, [buyer], request.sent + timedelta(hours=rng.randint(3, 30)), _body(
            f"Hello {buyer.first},",
            f"confirmed for {po['po_number']}: first delivery on {first.isoformat()}, {schedule}.",
            f"Kind regards,\n{danvik.first}",
        ))
        if rng.random() < 0.5:
            mailer.reply(reply, buyer, [danvik], reply.sent + timedelta(hours=rng.randint(1, 6)), _body(
                f"Thanks, {danvik.first}.",
                f"For our records: the order value of {po['po_number']} is {po['total_credits']:,.2f} credits, as agreed under contract {KDY['contract_id']}.",
                f"Best regards,\n{buyer.first}",
            ), label=CONFIDENTIAL)
        ctx.truth.offer_question(
            pool="comms:kdy-delivery-date", category="lookup",
            question=f"Which first delivery date did Kuat Drive Yards confirm for purchase order {po['po_number']}?",
            answer=first.isoformat(), sources=[ctx.truth.doc_source(reply.doc)],
        )
        confirmations.append((reply, po))
    days = Counter(reply.sent.date() for reply, _ in confirmations)
    for reply, po in confirmations:
        if days[reply.sent.date()] == 1:
            ctx.truth.offer_question(
                pool="comms:kdy-po-total", category="cross_source",
                question=f"What is the total value of the purchase order whose delivery schedule {danvik.name} confirmed on {reply.sent.date().isoformat()}?",
                answer=f"{po['po_number']}: {po['total_credits']:,.2f} credits", must_include=[po["po_number"], str(po["total_credits"])],
                sources=[ctx.truth.doc_source(reply.doc), ctx.truth.row_source("purchase_orders", po["sensitivity"], po_id=po["po_id"])],
            )

    open_orders = sorted((po for po in kdy_orders if po["status"] in ("OPEN", "PARTIAL")), key=lambda p: p["po_id"])
    buyer = _party(ctx.employee(max(kdy_orders, key=lambda p: (p["order_date"], p["po_id"]))["requested_by"]))
    rows = [["po_number", "order_date", "status", "total_credits"]] + [[po["po_number"], po["order_date"].isoformat(), po["status"], f"{po['total_credits']:.2f}"] for po in open_orders]
    count = f"{len(open_orders)} purchase orders"
    export = mailer.send(buyer, [danvik], _at(date(2026, 9, 28), 9, 30), "Open Kuat Drive Yards orders", _body(
        f"Hello {danvik.first},",
        f"ahead of next week's supplier review: {count} are still open or partially delivered. The list is attached.",
        f"Best regards,\n{buyer.first}",
    ), label=CONFIDENTIAL, attachment=("kdy-open-orders-2026-09-28.csv", _csv(rows)))
    ctx.truth.offer_question(
        pool="comms:kdy-open-orders", category="lookup",
        question="How many Kuat Drive Yards purchase orders were listed as open or partially delivered in the export Empire sent on 2026-09-28?",
        answer=count, sources=[ctx.truth.doc_source(export.doc)],
    )


def _supplier_thread(ctx: Context, mailer: _Mailer, rng, supplier: dict, po: dict, lines: list[dict], material: str) -> Mail:
    """One supplier exchange about an order; returns the supplier's reply."""
    contact = _supplier_party(supplier)
    asked = _office(rng, min(po["order_date"] + timedelta(days=rng.randint(20, 60)), AS_OF - timedelta(days=4)))
    if supplier["status"] != "ACTIVE":
        solberg = _party(ctx.person("solberg"))
        asked = _office(rng, date(2026, 8, 3) + timedelta(days=rng.randint(0, 40)))
        if supplier["status"] == "PROBATION":
            notice = f"following repeated late deliveries, {supplier['name']} is on probation in our supplier register from {asked.date().isoformat()}. We will review the status at the end of the quarter."
        else:
            notice = f"{supplier['name']} is suspended in our supplier register from {asked.date().isoformat()}. No new orders will be placed until the open quality issues are resolved."
        request = mailer.send(solberg, [contact], asked, f"Supplier status: {supplier['name']}", _body(f"Dear {contact.first},", notice, f"Regards,\n{solberg.first}"))
        answer = f"Understood. We have put a recovery plan in place and will send it to you by {(asked.date() + timedelta(days=10)).isoformat()}."
        return mailer.reply(request, contact, [solberg], asked + timedelta(hours=rng.randint(4, 48)), _body(f"Dear {solberg.first},", answer, f"Kind regards,\n{contact.first}"))
    topic = rng.choice(("delay", "certificate", "invoice"))
    if topic == "delay":
        sender = _party(ctx.employee(po["requested_by"]))
        moved = max(line["delivery_date"] for line in lines) + timedelta(days=rng.randint(7, 21))
        ask = f"could you give us an update on the delivery of purchase order {po['po_number']} ({material})?"
        answer = f"the delivery of {po['po_number']} moves to {moved.isoformat()} because of a {rng.choice(DELAY_REASONS)}. We apologise for the inconvenience."
        label, subject = INTERNAL, f"Delivery of {po['po_number']}"
    elif topic == "certificate":
        sender = _party(rng.choice(_people(ctx.personnel.active("QAT"), 5, 9, "en")))
        ask = f"please send the certificate of conformity for the {material} delivered under purchase order {po['po_number']}."
        answer = f"the certificate for {po['po_number']} will follow by {(asked.date() + timedelta(days=rng.randint(3, 10))).isoformat()}."
        label, subject = INTERNAL, f"Certificate of conformity for {po['po_number']}"
    else:
        sender = _party(rng.choice(_people(ctx.personnel.active("FIN"), 4, 9)))
        invoiced = round(po["total_credits"] * rng.choice((1.02, 1.05, 1.1)), 2)
        ask = f"your invoice for purchase order {po['po_number']} shows {invoiced:,.2f} credits, but the order total is {po['total_credits']:,.2f} credits. Could you send a corrected invoice?"
        answer = f"apologies for the error. A corrected invoice for {po['total_credits']:,.2f} credits follows today."
        label, subject = CONFIDENTIAL, f"Invoice query for {po['po_number']}"
    request = mailer.send(sender, [contact], asked, subject, _body(f"Hello {contact.first},", ask, f"Thanks,\n{sender.first}"), label=label)
    return mailer.reply(request, contact, [sender], asked + timedelta(hours=rng.randint(2, 40)), _body(f"Hello {sender.first},", answer, f"Kind regards,\n{contact.first}"))


def _supplier_mail(ctx: Context, mailer: _Mailer, index: _Index) -> None:
    rng = ctx.rng("comms:suppliers")
    contact_names = Counter(s["contact_name"] for s in ctx.supply.suppliers)
    orders: dict[str, list[dict]] = {}
    for po in ctx.supply.purchase_orders:
        if po["status"] != "CANCELLED" and date(2024, 6, 1) <= po["order_date"] <= AS_OF - timedelta(days=30):
            orders.setdefault(po["supplier_id"], []).append(po)
    for supplier in ctx.supply.suppliers:
        if supplier["supplier_id"] == KDY["supplier_id"] or supplier["supplier_id"] not in orders:
            continue
        po = rng.choice(orders[supplier["supplier_id"]])
        lines = index.po_lines[po["po_id"]]
        reply = _supplier_thread(ctx, mailer, rng, supplier, po, lines, index.materials[lines[0]["material_id"]]["name"])
        if contact_names[supplier["contact_name"]] == 1:
            ctx.truth.offer_question(
                pool="comms:supplier-register", category="cross_source",
                question=f"Which company does {supplier['contact_name']} work for, and what is that supplier's status in the supplier register?",
                answer=f"{supplier['name']}; {supplier['status']}", must_include=[supplier["name"], supplier["status"]],
                sources=[ctx.truth.doc_source(reply.doc), ctx.truth.row_source("suppliers", supplier["sensitivity"], supplier_id=supplier["supplier_id"])],
            )


# --------------------------------------------------------------------------
# Incidents on the station: the Zone Z17 beam shortage and the reactor temperature peak
# --------------------------------------------------------------------------

def _beam_orders(ctx: Context, index: _Index) -> list[dict]:
    """The quadanium beam orders that were due while Zone Z17 stalled, nearest to the start of the stall first."""
    beam_orders = list(dict.fromkeys(line["po_id"] for line in ctx.supply.po_lines
                                     if index.materials[line["material_id"]]["name"].startswith("Quadanium steel beam")))
    orders = [po for po in ctx.supply.purchase_orders if po["po_id"] in beam_orders and po["status"] != "CANCELLED" and po["order_date"] < STALL_START]
    due = [po for po in orders if STALL_START <= max(line["delivery_date"] for line in index.po_lines[po["po_id"]]) <= STALL_END + timedelta(days=15)]
    return sorted(due or orders, key=lambda po: (abs((po["order_date"] - STALL_START).days), po["po_id"]))[:2]


def _beam_shortage(ctx: Context, mailer: _Mailer, index: _Index) -> None:
    rng = ctx.rng("comms:beam-shortage")
    orders = _beam_orders(ctx, index)
    zone = _party(rng.choice(_people(ctx.personnel.active("CON"), 10, 11, "en") or _people(ctx.personnel.active("CON"), 10, 11)))
    brandt, stroud, solberg = (_party(ctx.person(handle)) for handle in ("brandt", "stroud", "solberg"))
    buyer = _party(ctx.employee(orders[0]["requested_by"]))
    supplier = index.suppliers[orders[0]["supplier_id"]]["name"]
    listed = " and ".join(f"{po['po_number']} ({index.suppliers[po['supplier_id']]['name']})" for po in orders)
    resumed_on = STALL_END + timedelta(days=1)
    alert = mailer.send(zone, [brandt, stroud], _at(date(2026, 4, 3), 9, 12), f"Zone {STALLED_ZONE}: quadanium steel beam shortage", _body(
        f"Hello {brandt.first}, hello {stroud.first},",
        f"construction in Zone {STALLED_ZONE} has almost stopped since {STALL_START.isoformat()}: the quadanium steel beams for the band have not arrived. From 2026-04-06 we keep a reduced crew on {STALLED_ZONE} and move the other crews to the neighbouring zones.",
        f"Regards,\n{zone.first}",
    ), cc=[buyer])
    chase = mailer.reply(alert, buyer, [zone, brandt, stroud], _at(date(2026, 4, 7), 10, 40), _body(
        "Hello all,",
        f"the open beam orders are {listed}. {supplier} reports an outage at its rolling mill; I have asked for a recovery date.",
        f"Regards,\n{buyer.first}",
    ))
    expedite = mailer.reply(chase, solberg, [buyer, zone], _at(date(2026, 5, 12), 16, 5), _body(
        f"Hello {buyer.first},",
        f"I approved expediting {orders[0]['po_number']} today. {supplier} expects a partial delivery in early June.",
        f"Regards,\n{solberg.first}",
    ))
    resumed = mailer.reply(expedite, zone, [brandt, stroud, solberg, buyer], _at(date(2026, 7, 2), 8, 30), _body(
        "Hello all,",
        f"the beams have arrived and Zone {STALLED_ZONE} has been back on a full crew since {resumed_on.isoformat()}.",
        f"Regards,\n{zone.first}",
    ))
    for question, answer, mail in (
        ("Which construction zone stalled because of the quadanium steel beam shortage in spring 2026?", STALLED_ZONE, alert),
        (f"Which purchase order did {solberg.name} approve for expediting during the quadanium steel beam shortage?", orders[0]["po_number"], expedite),
        (f"Since what date has Zone {STALLED_ZONE} been back on a full crew after the quadanium steel beam shortage?", resumed_on.isoformat(), resumed),
    ):
        ctx.truth.offer_question(pool="comms:beam-shortage", category="lookup", question=question, answer=answer, sources=[ctx.truth.doc_source(mail.doc)])


def _reactor_engineer(ctx: Context) -> Employee:
    """The engineer on shift when the reactor temperature peaked; mail and chat both use them."""
    return _people(ctx.personnel.active("RPS"), 6, 9, "en")[0]


def _approved_core_temperature() -> tuple[str, str, str]:
    """(document number, approved revision, approved value) of the reactor core vessel's design core temperature."""
    number = next(n for n, spec in canon.CONFLICTING_SPECS.items() if spec[:2] == ("HR", "RCV"))
    unit, revisions = canon.CONFLICTING_SPECS[number][3:]
    revision, (value, _) = next((rev, entry) for rev, entry in revisions.items() if entry[1] == "APPROVED")
    return number, revision, f"{value:,} {unit}"


def _reactor_peak(ctx: Context, mailer: _Mailer) -> None:
    engineer, kestrel, quayle = _party(_reactor_engineer(ctx)), _party(ctx.person("kestrel")), _party(ctx.person("quayle"))
    number, revision, approved = _approved_core_temperature()
    peak_day = PEAK_AT.date()
    report = mailer.send(engineer, [kestrel], PEAK_AT + timedelta(minutes=12), f"{PEAK_SENSOR} temperature peak on {peak_day.isoformat()}", _body(
        f"Hello {kestrel.first},",
        f"{PEAK_SENSOR} peaked at {PEAK_VALUE} K at {PEAK_AT:%H:%M} UTC today, above the approved design core temperature of {approved} in {number} Rev {revision}. "
        f"{FOLLOWER_SENSOR} at the heat exchanger outlet rose to {FOLLOWER_PEAK} K at the same time. We are checking the coolant loop.",
        f"Regards,\n{engineer.first}",
    ), label=CONFIDENTIAL, cc=[REACTOR_OPS])
    facilities = mailer.reply(report, quayle, [engineer, kestrel, REACTOR_OPS], PEAK_AT + timedelta(minutes=47), _body(
        "Hello both,",
        f"Facilities logged incident {PEAK_INCIDENT['incident_id']} at the same time: {PEAK_INCIDENT['summary']}",
        f"Regards,\n{quayle.first}",
    ))
    mailer.reply(facilities, kestrel, [engineer, quayle, REACTOR_OPS], PEAK_AT + timedelta(hours=2, minutes=5), _body(
        "Thanks both.",
        f"We will hold the root-cause review with Thermal Systems on {_weekday(peak_day + timedelta(days=1)).isoformat()}. Please keep the trend data for the review.",
        kestrel.first,
    ))
    ctx.truth.offer_question(
        pool="comms:reactor-peak", category="cross_source",
        question=f"Which facility incident coincided with the reactor core temperature peak on {peak_day.isoformat()}, and how long was the coolant pump down?",
        answer=f"{PEAK_INCIDENT['incident_id']}; the pump was restarted after 40 minutes", must_include=[PEAK_INCIDENT["incident_id"], "40 minutes"],
        sources=[ctx.truth.doc_source(facilities.doc), ctx.truth.row_source("facility_incidents", PEAK_INCIDENT["sensitivity"], incident_id=PEAK_INCIDENT["incident_id"])],
    )
    ctx.truth.offer_question(
        pool="comms:reactor-peak-value", category="lookup",
        question=f"What peak temperature did {PEAK_SENSOR} reach on {peak_day.isoformat()}, according to the reactor team's mail?",
        answer=f"{PEAK_VALUE} K", sources=[ctx.truth.doc_source(report.doc)],
    )


# --------------------------------------------------------------------------
# Quality follow-ups on non-conformance and test reports
# --------------------------------------------------------------------------

def _ncr_followups(ctx: Context, mailer: _Mailer, ncrs: list[Doc]) -> None:
    rng = ctx.rng("comms:ncr")
    asked = []
    english = [d for d in ncrs if d.language == "en"]
    for ncr in sorted(rng.sample(english, min(18, len(english))), key=lambda d: d.doc_number):
        day = _weekday(ncr.created_date + timedelta(days=rng.randint(3, 25)))
        if day > AS_OF:
            continue
        dept = canon.SYSTEMS[ncr.system_code]["dept"]
        sender = _party(rng.choice(_people(ctx.personnel.active(dept), 10, 11, "en") or _people(ctx.personnel.active(dept), 9, 12)))
        recipient = _party(ctx.employee(ncr.approver_id))
        request = mailer.send(sender, [recipient], _at(day, rng.randint(8, 17), rng.randrange(60)), f"Status of {ncr.doc_number}", _body(
            f"Hello {recipient.first},",
            f"what is the status of {ncr.doc_number}? We need the disposition before the next integration step on the affected hardware.",
            f"Thanks,\n{sender.first}",
        ))
        mailer.reply(request, recipient, [sender], request.sent + timedelta(hours=rng.randint(2, 26)), _body(
            f"Hello {sender.first},",
            f"{ncr.doc_number} is with the review board. I will update the report as soon as the disposition is signed.",
            f"Regards,\n{recipient.first}",
        ))
        asked.append((request, sender, recipient, ncr))
    keys = Counter((sender.name, request.sent.date()) for request, sender, _, _ in asked)
    for request, sender, recipient, ncr in asked:
        if keys[(sender.name, request.sent.date())] == 1:
            ctx.truth.offer_question(
                pool="comms:ncr-raised-by", category="cross_source",
                question=f"Who raised the non-conformance report that {sender.name} asked {recipient.name} about on {request.sent.date().isoformat()}?",
                answer=ncr.author_name, sources=[ctx.truth.doc_source(request.doc), ctx.truth.doc_source(ncr)],
            )

    crew = _people(ctx.personnel.german_speakers(), 8, 11)
    german = [d for d in ncrs if d.language == "de"]
    for ncr in sorted(rng.sample(german, min(4, len(german))), key=lambda d: d.doc_number):
        author = _party(ctx.employee(ncr.author_id))
        sender = _party(rng.choice([e for e in crew if e.employee_id != ncr.author_id]))
        day = _weekday(min(ncr.created_date + timedelta(days=rng.randint(2, 12)), AS_OF - timedelta(days=3)))
        request = mailer.send(sender, [author], _at(day, rng.randint(6, 15), rng.randrange(60)), f"Nacharbeit zu {ncr.doc_number}", _body(
            f"Hallo {author.first},",
            f"wie ist der Stand der Nacharbeit zu {ncr.doc_number}? Der Bereich soll nächste Woche zur Abnahme. Bitte gib mir bis {de_date(day + timedelta(days=3))} Bescheid.",
            f"Danke und Gruß\n{sender.first}",
        ), language="de")
        mailer.reply(request, author, [sender], request.sent + timedelta(hours=rng.randint(2, 20)), _body(
            f"Hallo {sender.first},",
            f"die Nacharbeit ist eingeplant, Schicht B übernimmt das am {de_date(day + timedelta(days=2))}. Ich melde mich, sobald die Nachprüfung durch ist.",
            f"Gruß\n{author.first}",
        ))


def _test_followups(ctx: Context, mailer: _Mailer, tests: list[Doc]) -> None:
    rng = ctx.rng("comms:tests")
    integrators = _people(ctx.personnel.active("PMO"), 9, 11)
    asked = []
    english = [d for d in tests if d.language == "en" and d.fmt == "md" and d.author_id != d.approver_id]
    for test in sorted(rng.sample(english, min(18, len(english))), key=lambda d: d.doc_number):
        day = _weekday(test.created_date + timedelta(days=rng.randint(1, 10)))
        if day > AS_OF:
            continue
        sender, recipient = _party(rng.choice(integrators)), _party(ctx.employee(test.approver_id))
        review = _weekday(day + timedelta(days=rng.randint(7, 21)))
        request = mailer.send(sender, [recipient], _at(day, rng.randint(8, 17), rng.randrange(60)), f"Signature needed: {test.doc_number}", _body(
            f"Hello {recipient.first},",
            f"please sign test report {test.doc_number} as witness and file it for the integration review on {review.isoformat()}.",
            f"Thanks,\n{sender.first}",
        ))
        mailer.reply(request, recipient, [sender], request.sent + timedelta(hours=rng.randint(1, 30)), _body(
            f"Hello {sender.first},", "signed and filed.", f"Regards,\n{recipient.first}",
        ))
        asked.append((request, sender, recipient, test))
    keys = Counter((sender.name, recipient.name, request.sent.date()) for request, sender, recipient, _ in asked)
    for request, sender, recipient, test in asked:
        if keys[(sender.name, recipient.name, request.sent.date())] != 1:
            continue
        when = request.sent.date().isoformat()
        ctx.truth.offer_question(
            pool="comms:test-report-number", category="lookup",
            question=f"Which test report did {sender.name} ask {recipient.name} to sign on {when}?",
            answer=test.doc_number, sources=[ctx.truth.doc_source(request.doc)],
        )
        ctx.truth.offer_question(
            pool="comms:test-report-tester", category="cross_source",
            question=f"Who performed the test documented in the report that {sender.name} asked {recipient.name} to sign on {when}?",
            answer=test.author_name, sources=[ctx.truth.doc_source(request.doc), ctx.truth.doc_source(test)],
        )

    german = [d for d in tests if d.language == "de"]
    crew = _people(ctx.personnel.german_speakers(), 8, 11)
    for test in sorted(rng.sample(german, min(4, len(german))), key=lambda d: d.doc_number):
        tester = _party(ctx.employee(test.author_id))
        sender = _party(rng.choice([e for e in crew if e.employee_id != test.author_id]))
        day = _weekday(min(test.created_date + timedelta(days=rng.randint(1, 6)), AS_OF - timedelta(days=3)))
        request = mailer.send(sender, [tester], _at(day, rng.randint(6, 15), rng.randrange(60)), f"Prüfbericht {test.doc_number} unterschreiben", _body(
            f"Hallo {tester.first},",
            f"kannst du den Prüfbericht {test.doc_number} bitte unterschreiben und in die Integrationsakte legen? Die Integrationsprüfung ist am {de_date(day + timedelta(days=9))}.",
            f"Danke\n{sender.first}",
        ), language="de")
        mailer.reply(request, tester, [sender], request.sent + timedelta(hours=rng.randint(1, 8)), _body(
            f"Hallo {sender.first},", "erledigt, liegt in der Akte.", f"Gruß\n{tester.first}",
        ))


# --------------------------------------------------------------------------
# People: farewells and welcomes
# --------------------------------------------------------------------------

def _farewells(ctx: Context, mailer: _Mailer) -> None:
    rng = ctx.rng("comms:farewells")
    leavers = [e for e in ctx.personnel.employees
               if not e.is_active and e.handle is None and date(2025, 1, 1) <= e.termination_date <= AS_OF]
    for leaver in sorted(rng.sample(leavers, min(15, len(leavers))), key=lambda e: e.employee_id):
        colleagues = [e for e in ctx.personnel.active(leaver.department) if e.employee_id != leaver.manager_id]
        manager = ctx.employee(leaver.manager_id)
        recipients = [_party(e) for e in rng.sample(colleagues, min(3, len(colleagues)))] + [_party(manager)]
        last_day = leaver.termination_date
        sent = _at(max(leaver.hire_date, last_day - timedelta(days=2)), rng.randint(9, 16), rng.randrange(60))
        years = max(1, (last_day - leaver.hire_date).days // 365)
        german = leaver.language == "de"
        if leaver.termination_reason == "Contract ended":
            sender = _party(manager)
            if german:
                body = _body("Hallo zusammen,", f"der Vertrag von {leaver.name} endet am {de_date(last_day)}. Vielen Dank, {leaver.first_name}, für die gute Arbeit!", f"Viele Grüße\n{sender.first}")
            else:
                body = _body("Dear all,", f"{leaver.name}'s contract with us ends on {last_day.isoformat()}. Please join me in thanking {leaver.first_name} for the work in {canon.DEPT_NAME[leaver.department]}.", f"Best regards,\n{sender.first}")
            recipients = [r for r in recipients if r.employee_id != manager.employee_id] + [_party(leaver)]
        else:
            sender = _party(leaver)
            reason_en, reason_de = FAREWELL_REASONS[leaver.termination_reason]
            if german:
                body = _body("Hallo zusammen,", f"am {de_date(last_day)} ist mein letzter Arbeitstag in der {canon.GERMAN_SITE_DE}. {reason_de.format(years=years)} Vielen Dank für die gute Zusammenarbeit!", f"Macht's gut\n{sender.first}")
            else:
                body = _body("Dear all,", f"my last day at {canon.COMPANY} is {last_day.isoformat()}. {reason_en.format(years=years)}", "Thank you for the great teamwork, and stay in touch!", f"All the best,\n{sender.first}")
        mail = mailer.send(sender, recipients, sent, "Abschied" if german else f"Farewell from {leaver.name}", body, language="de" if german else "en")
        ctx.truth.offer_question(
            pool="comms:farewell-date", category="cross_source",
            question=f"When was {leaver.name}'s last day at {canon.COMPANY}?", answer=last_day.isoformat(),
            sources=[ctx.truth.doc_source(mail.doc), ctx.truth.row_source("employees", INTERNAL, employee_id=leaver.employee_id)],
        )


def _welcomes(ctx: Context, mailer: _Mailer) -> None:
    rng = ctx.rng("comms:welcomes")
    joiners = [e for e in ctx.personnel.active() if e.handle is None and date(2025, 9, 1) <= e.hire_date <= AS_OF]
    for joiner in sorted(rng.sample(joiners, min(15, len(joiners))), key=lambda e: e.employee_id):
        manager = _party(ctx.employee(joiner.manager_id))
        team = [e for e in ctx.personnel.active(joiner.department) if e.hire_date < joiner.hire_date and e.employee_id not in (joiner.employee_id, joiner.manager_id)]
        recipients = [_party(e) for e in rng.sample(team, min(4, len(team)))]
        sent = _office(rng, joiner.hire_date - timedelta(days=4))
        if joiner.language == "de":
            mail = mailer.send(manager, recipients, sent, f"Herzlich willkommen, {joiner.name}!", _body(
                "Hallo zusammen,",
                f"ab dem {de_date(joiner.hire_date)} verstärkt {joiner.name} unser Team als {joiner.title}. Bitte nehmt {joiner.first_name} freundlich auf.",
                f"Viele Grüße\n{manager.first}",
            ), language="de")
        else:
            mail = mailer.send(manager, recipients, sent, f"Welcome {joiner.name}", _body(
                "Hello team,",
                f"please welcome {joiner.name}, who joins {canon.DEPT_NAME[joiner.department]} as {joiner.title} on {joiner.hire_date.isoformat()}.",
                f"Best regards,\n{manager.first}",
            ))
        ctx.truth.offer_question(
            pool="comms:new-joiner", category="cross_source",
            question=f"On what date did {joiner.name} join {canon.COMPANY}, and who announced the arrival to the team?",
            answer=f"{joiner.hire_date.isoformat()}; {manager.name}", must_include=[joiner.hire_date.isoformat(), manager.name],
            sources=[ctx.truth.doc_source(mail.doc), ctx.truth.row_source("employees", INTERNAL, employee_id=joiner.employee_id)],
        )


# --------------------------------------------------------------------------
# Routine engineering and business mail
# --------------------------------------------------------------------------

def _work_package_mail(ctx: Context, mailer: _Mailer) -> None:
    rng = ctx.rng("comms:work-packages")
    schedulers = _people(ctx.personnel.active("PMO"), 4, 8)
    milestones: dict[str, list[dict]] = {}
    for row in ctx.programs.milestones:
        if row["wp_id"]:
            milestones.setdefault(row["wp_id"], []).append(row)
    candidates = [wp for wp in ctx.programs.work_packages
                  if wp.program_id == canon.MAIN_PROGRAM and wp.status == "IN_PROGRESS" and wp.start_date <= AS_OF - timedelta(days=150)
                  and ctx.employee(wp.owner_id).is_active]
    reports = []
    for wp in sorted(rng.sample(candidates, min(35, len(candidates))), key=lambda w: w.wp_id):
        owner, scheduler = _party(ctx.employee(wp.owner_id)), _party(rng.choice(schedulers))
        span = (AS_OF - timedelta(days=45) - wp.start_date).days
        sent = _office(rng, wp.start_date + timedelta(days=int(span * rng.uniform(0.4, 1.0))))
        day = sent.date()
        progress = progress_on(wp, day)
        upcoming = sorted((m for m in milestones.get(wp.wp_id, []) if m["forecast_date"] > day), key=lambda m: (m["forecast_date"], m["milestone_id"]))
        paragraphs = [f"Hello {scheduler.first},", f"status of {wp.wp_id} ({wp.name}) as of {day.isoformat()}: {progress}% complete."]
        if upcoming:
            paragraphs.append(f"Next milestone: {upcoming[0]['name']}, forecast {upcoming[0]['forecast_date'].isoformat()}.")
        confidential = rng.random() < 0.4
        if confidential:
            spent = round(wp.actual_mcr * progress / wp.percent_complete, 2) if wp.percent_complete else 0.0
            paragraphs.append(f"Spend to date is {spent:,.2f} Mcr against a budget of {wp.budget_mcr:,.2f} Mcr.")
        paragraphs.append(f"Regards,\n{owner.first}")
        report = mailer.send(owner, [scheduler], sent, f"{wp.wp_id} status update", _body(*paragraphs), label=CONFIDENTIAL if confidential else INTERNAL)
        mailer.reply(report, scheduler, [owner], sent + timedelta(hours=rng.randint(1, 20)), _body(
            f"Thanks, {owner.first}.", "I have updated the schedule for the weekly program review.", f"Regards,\n{scheduler.first}",
        ))
        reports.append((report, owner, wp, upcoming[0] if upcoming else None))
    keys = Counter((owner.name, report.sent.date()) for report, owner, _, _ in reports)
    for report, owner, wp, milestone in reports:
        day = report.sent.date().isoformat()
        if keys[(owner.name, report.sent.date())] == 1:
            ctx.truth.offer_question(
                pool="comms:wp-progress", category="cross_source",
                question=f"What is the current percent complete of the work package that {owner.name} reported on in the status mail of {day}?",
                answer=f"{wp.wp_id}: {wp.percent_complete}%", must_include=[wp.wp_id, str(wp.percent_complete)],
                sources=[ctx.truth.doc_source(report.doc), ctx.truth.row_source("work_packages", wp.sensitivity, wp_id=wp.wp_id)],
            )
        if milestone:
            ctx.truth.offer_question(
                pool="comms:wp-milestone", category="lookup",
                question=f"In the status mail for {wp.wp_id} sent on {day}, what forecast date did {owner.name} give for the next milestone?",
                answer=milestone["forecast_date"].isoformat(), sources=[ctx.truth.doc_source(report.doc)],
            )


def _spec_reviews(ctx: Context, mailer: _Mailer) -> None:
    rng = ctx.rng("comms:spec-reviews")
    components = [c for c in ctx.engineering.components if not c.planted_spec and c.engineer_id != c.approver_id]
    for comp in sorted(rng.sample(components, min(15, len(components))), key=lambda c: c.code):
        engineer, approver = _party(ctx.employee(comp.engineer_id)), _party(ctx.employee(comp.approver_id))
        spec = f"{comp.spec_number} Rev {comp.spec_revision}"
        request = mailer.send(engineer, [approver], _office(rng, comp.spec_date - timedelta(days=rng.randint(5, 20))), f"Review request: {spec}", _body(
            f"Hello {approver.first},",
            f"{spec} ({comp.name} Specification) is ready for your review. The changes from the previous revision are listed in the revision history.",
            f"Thanks,\n{engineer.first}",
        ))
        reply = mailer.reply(request, approver, [engineer], _at(comp.spec_date, rng.randint(9, 17), rng.randrange(60)), _body(
            f"Hello {engineer.first},",
            f"I approved {spec} today ({comp.spec_date.isoformat()}). Please release it to the document registry.",
            f"Regards,\n{approver.first}",
        ))
        ctx.truth.offer_question(
            pool="comms:spec-approval", category="lookup",
            question=f"On what date did {approver.name} approve {spec}, according to the review thread?",
            answer=comp.spec_date.isoformat(), sources=[ctx.truth.doc_source(reply.doc)],
        )


def _po_approvals(ctx: Context, mailer: _Mailer, index: _Index) -> None:
    rng = ctx.rng("comms:po-approvals")
    orders = [po for po in ctx.supply.purchase_orders
              if po["requested_by"] != po["approved_by"] and date(2024, 6, 1) <= po["order_date"] <= AS_OF - timedelta(days=5)]
    for po in sorted(rng.sample(orders, min(15, len(orders))), key=lambda p: p["po_id"]):
        buyer, approver = _party(ctx.employee(po["requested_by"])), _party(ctx.employee(po["approved_by"]))
        supplier = index.suppliers[po["supplier_id"]]["name"]
        lines = index.po_lines[po["po_id"]]
        request = mailer.send(buyer, [approver], _office(rng, po["order_date"] - timedelta(days=2)), f"Approval request: {po['po_number']}", _body(
            f"Hello {approver.first},",
            f"please approve purchase order {po['po_number']} to {supplier}: {len(lines)} line(s) for work package {po['wp_id']}, total {po['total_credits']:,.2f} credits.",
            f"Thanks,\n{buyer.first}",
        ), label=CONFIDENTIAL)
        reply = mailer.reply(request, approver, [buyer], _at(po["order_date"], rng.randint(8, 17), rng.randrange(60)), _body(
            f"Hello {buyer.first},", f"approved. Please release {po['po_number']} to {supplier}.", f"Regards,\n{approver.first}",
        ))
        ctx.truth.offer_question(
            pool="comms:po-approver", category="cross_source",
            question=f"Who approved purchase order {po['po_number']}, and what is its status today?",
            answer=f"{approver.name}; {po['status']}", must_include=[approver.name, po["status"]],
            sources=[ctx.truth.doc_source(reply.doc), ctx.truth.row_source("purchase_orders", po["sensitivity"], po_id=po["po_id"])],
        )


def _notices(ctx: Context, mailer: _Mailer) -> None:
    rng = ctx.rng("comms:notices")
    it_leads = _people(ctx.personnel.active("CCS"), 10, 11)
    safety = _people(ctx.personnel.active("FAC"), 5, 9)
    span = (AS_OF - TICKETS_START).days - 12
    announced = []
    for _ in range(12):
        sender = _party(rng.choice(it_leads))
        sent = _office(rng, TICKETS_START + timedelta(days=rng.randint(0, span)))
        service = rng.choice(MAINTENANCE_SERVICES)
        day = _weekday(sent.date() + timedelta(days=rng.randint(3, 9)))
        mail = mailer.send(sender, [ALL_STAFF], sent, f"Planned maintenance: {service}", _body(
            "Dear colleagues,",
            f"the {service} will be unavailable on {day.isoformat()} from 22:00 to 02:00 UTC for planned maintenance. Please save your work before 22:00.",
            f"Thank you,\n{sender.first}",
        ))
        announced.append((f"the planned maintenance of the {service}", day, mail))
    for site, german in ((canon.HQ, False), (canon.STATION, False), (canon.GERMAN_SITE, True)):
        for year in (2025, 2026):
            sender = _party(rng.choice(safety))
            sent = _office(rng, date(year, rng.randint(3, 9), rng.randint(1, 20)))
            day = _weekday(sent.date() + timedelta(days=rng.randint(7, 14)))
            if german:
                mailer.send(sender, [ERIADU_TEAM], sent, f"Räumungsübung am {de_date(day)}", _body(
                    "Hallo zusammen,",
                    f"am {de_date(day)} um 10:00 Uhr findet in der {canon.GERMAN_SITE_DE} eine Räumungsübung statt. Bitte folgt den Anweisungen der Ersthelfer und sammelt euch am Tor 3.",
                    f"Danke\n{sender.first}",
                ), language="de")
                continue
            mail = mailer.send(sender, [ALL_STAFF], sent, f"Evacuation drill at {site}", _body(
                "Dear colleagues,",
                f"an evacuation drill takes place at {site} on {day.isoformat()} at 10:00. Please follow the instructions of the floor wardens.",
                f"Thank you,\n{sender.first}",
            ))
            announced.append((f"the evacuation drill at {site}", day, mail))
    keys = Counter((what, mail.sent.date()) for what, _, mail in announced)
    for what, day, mail in announced:
        if keys[(what, mail.sent.date())] == 1:
            ctx.truth.offer_question(
                pool="comms:notice", category="lookup",
                question=f"On what date is {what} that was announced on {mail.sent.date().isoformat()}?",
                answer=day.isoformat(), sources=[ctx.truth.doc_source(mail.doc)],
            )

    amaranth = _party(ctx.person("amaranth"))
    for _ in range(5):
        sent = _office(rng, date(2025, 3, 3) + timedelta(days=rng.randint(0, 540)))
        floor_from, floor_to = rng.sample(range(30, 48), 2)
        mailer.send(amaranth, [ALL_STAFF], sent, f"Office consolidation: floor {floor_from} moves to floor {floor_to}", _body(
            "Dear colleagues,",
            f"as part of the {canon.HQ} office consolidation, the teams on floor {floor_from} move to floor {floor_to} on {_weekday(sent.date() + timedelta(days=12)).isoformat()}. Crates are delivered two days before the move.",
            f"Best regards,\n{amaranth.first}",
        ))
    trainers = _people(ctx.personnel.active("HRA"), 4, 9)
    for _ in range(5):
        sender = _party(rng.choice(trainers))
        sent = _office(rng, TICKETS_START + timedelta(days=rng.randint(0, span)))
        sessions = [_weekday(sent.date() + timedelta(days=7 * n + 2)).isoformat() for n in (1, 2, 3)]
        mailer.send(sender, [ALL_STAFF], sent, "Workplace safety refresher sessions", _body(
            "Dear colleagues,",
            "the annual workplace safety refresher is open for booking. Sessions take 90 minutes and run on:",
            sessions,
            f"Please book through your manager.\n{sender.first}",
        ))


def _eriadu_mail(ctx: Context, mailer: _Mailer, index: _Index) -> None:
    rng = ctx.rng("comms:eriadu")
    crew = _people(ctx.personnel.german_speakers(), 4, 9)
    crew_con = [e for e in crew if e.department == "CON"]
    received = [(po, line) for po in ctx.supply.purchase_orders if po["status"] == "RECEIVED"
                for line in index.po_lines[po["po_id"]][:1] if TICKETS_START <= line["delivery_date"] <= AS_OF]
    for po, line in sorted(rng.sample(received, min(12, len(received))), key=lambda pair: pair[0]["po_id"]):
        sender = _party(rng.choice(crew_con))
        material = index.materials[line["material_id"]]
        quantity = f"{line['quantity']} {UNITS_DE.get(material['unit'], material['unit'])}"
        sent = _at(line["delivery_date"], rng.randint(6, 15), rng.randrange(60))
        mail = mailer.send(sender, [ERIADU_TEAM], sent, f"Wareneingang zu Bestellung {po['po_number']}", _body(
            "Hallo zusammen,",
            f"heute sind {quantity} {material['name']} zu Bestellung {po['po_number']} in der Fertigungswerft angekommen. "
            f"Die Ware liegt in Halle {rng.randint(1, 6)} und ist für Arbeitspaket {po['wp_id']} vorgesehen. Bitte bis Schichtende einlagern.",
            f"Gruß\n{sender.first}",
        ), language="de")
        ctx.truth.offer_question(
            pool="comms:eriadu-delivery", category="lookup",
            question=f"According to the Eriadu yard's goods-receipt mail of {sent.date().isoformat()} for purchase order {po['po_number']}, how much {material['name']} arrived?",
            answer=quantity, sources=[ctx.truth.doc_source(mail.doc)],
        )
    for monday in sorted(rng.sample([_nth_weekday(2026, month, 0, 2) for month in range(1, 10)], 6)):
        sender = _party(rng.choice(crew_con))
        shifts = rng.sample(crew_con, 9)
        mailer.send(sender, [ERIADU_TEAM], _at(monday - timedelta(days=3), 12, rng.randrange(60)), f"Schichtplan KW {monday.isocalendar().week}", _body(
            "Hallo zusammen,",
            f"hier der Schichtplan für KW {monday.isocalendar().week}:",
            [f"Schicht {name} ({hours}): {', '.join(e.name for e in shifts[n * 3:n * 3 + 3])}"
             for n, (name, hours) in enumerate((("A", "06:00–14:00"), ("B", "14:00–22:00"), ("C", "22:00–06:00")))],
            f"Gruß\n{sender.first}",
        ), language="de")
    for _ in range(4):
        sender = _party(rng.choice(crew_con))
        sent = _office(rng, date(2025, 2, 3) + timedelta(days=rng.randint(0, 590)))
        crane, hall, day = rng.randint(1, 4), rng.randint(1, 6), _weekday(sent.date() + timedelta(days=rng.randint(3, 10)))
        mailer.send(sender, [ERIADU_TEAM], sent, f"Portalkran {crane}: Wartung am {de_date(day)}", _body(
            "Hallo zusammen,",
            f"der Portalkran {crane} in Halle {hall} wird am {de_date(day)} von 06:00 bis 14:00 Uhr gewartet. In dieser Zeit bitte keine Hübe einplanen.",
            f"Gruß\n{sender.first}",
        ), language="de")
    for _ in range(3):
        sender = _party(rng.choice(crew_con))
        sent = _office(rng, date(2025, 2, 3) + timedelta(days=rng.randint(0, 590)))
        day = _weekday(sent.date() + timedelta(days=rng.randint(4, 12)))
        mailer.send(sender, [ERIADU_TEAM], sent, "Werkzeugausgabe wegen Inventur geschlossen", _body(
            "Hallo zusammen,",
            f"die Werkzeugausgabe bleibt am {de_date(day)} wegen Inventur geschlossen. Bitte benötigtes Werkzeug am Vortag abholen.",
            f"Gruß\n{sender.first}",
        ), language="de")


def _sender_departments(ctx: Context, mails: list[Mail]) -> None:
    rng = ctx.rng("comms:sender-departments")
    keys = Counter((mail.doc.title, mail.sent.date()) for mail in mails)
    candidates = [mail for mail in mails if mail.sender.employee_id and ctx.employee(mail.sender.employee_id).is_active
                  and mail.doc.language == "en" and keys[(mail.doc.title, mail.sent.date())] == 1]
    for mail in rng.sample(candidates, min(15, len(candidates))):
        employee = ctx.employee(mail.sender.employee_id)
        department = canon.DEPT_NAME[employee.department]
        ctx.truth.offer_question(
            pool="comms:sender-dept", category="cross_source",
            question=f"Which department does the sender of the mail \"{mail.doc.title}\" sent on {mail.sent.date().isoformat()} work in today?",
            answer=department,
            sources=[ctx.truth.doc_source(mail.doc), ctx.truth.row_source("employees", INTERNAL, employee_id=employee.employee_id),
                     ctx.truth.row_source("departments", INTERNAL, department_id=canon.DEPT_ID[employee.department])],
        )


# --------------------------------------------------------------------------
# Tickets
# --------------------------------------------------------------------------

def _duration(rng) -> timedelta:
    roll = rng.random()
    if roll < 0.55:
        return timedelta(hours=rng.randint(1, 48))
    if roll < 0.85:
        return timedelta(days=rng.randint(2, 14), hours=rng.randint(0, 8))
    return timedelta(days=rng.randint(15, 75))


def _status_at(ticket: dict, moment: datetime) -> str:
    if ticket["resolved"] and ticket["resolved"] <= moment:
        return "RESOLVED"
    return "OPEN" if moment - ticket["created"] < timedelta(hours=4) else "IN_PROGRESS"


def _ticket_drafts(ctx: Context, rng) -> list[dict]:
    active, german = ctx.personnel.active(), ctx.personnel.german_speakers()
    regulars = rng.sample(_people(active, 2, 11), 12)  # people who raise many tickets
    agents = {"IT_HELPDESK": rng.sample(_people(ctx.personnel.active("CCS"), 2, 8), 6), "FACILITIES": rng.sample(_people(ctx.personnel.active("FAC"), 2, 8), 5)}
    programs = [p["name"] for p in ctx.programs.programs]
    span = (AS_OF - TICKETS_START).days
    drafts = []
    for _ in range(200):
        queue = "IT_HELPDESK" if rng.random() < 0.65 else "FACILITIES"
        language = "de" if rng.random() < 0.1 else "en"
        subject, description, resolution = rng.choice(TICKET_TOPICS[(queue, language)])
        fill = {"room": rng.choice(ROOMS), "floor": rng.randint(2, 60), "tool": rng.choice(TOOLS), "place": rng.choice(PLACES),
                "program": rng.choice(programs), "hall": rng.randint(1, 6)}
        if language == "de":
            requester = rng.choice(german)
        else:
            requester = rng.choice(regulars) if rng.random() < 0.35 else rng.choice(active)
        created = _at(TICKETS_START + timedelta(days=rng.randrange(span)), rng.randint(7, 17), rng.randrange(60))
        resolved = created + _duration(rng)
        drafts.append({
            "queue": queue, "subject": subject.format(**fill), "description": description.format(**fill), "resolution": resolution,
            "priority": rng.choices(("LOW", "MEDIUM", "HIGH"), weights=(45, 40, 15), k=1)[0], "requester": requester,
            "assignee": rng.choice(agents[queue]), "created": created, "resolved": resolved if resolved <= EXPORTED_AT else None,
            "related_incident": None, "language": language,
        })
    for incident in ctx.facilities.incidents:
        if incident["opened_date"] < TICKETS_START:
            continue
        drafts.append({
            "queue": "FACILITIES", "subject": f"Facility incident {incident['incident_id']}",
            "description": f"Logged from the facilities hotline. The details are recorded in facility incident {incident['incident_id']}.",
            "resolution": "Incident closed by Facilities & Workplace Safety.", "priority": "HIGH" if incident["severity"] == "MEDIUM" else "MEDIUM",
            "requester": ctx.employee(incident["reported_by"]), "assignee": rng.choice(agents["FACILITIES"]),
            "created": _at(incident["opened_date"], rng.randint(8, 16), rng.randrange(60)),
            "resolved": _at(incident["closed_date"], 17) if incident["closed_date"] else None,
            "related_incident": incident["incident_id"], "language": "en",
        })
    return drafts


def _ticket_json(ticket: dict, rng) -> dict:
    created, resolved = ticket["created"], ticket["resolved"]
    first_touch = created + timedelta(minutes=rng.randint(10, 240))
    if resolved:
        first_touch = min(first_touch, created + (resolved - created) / 2)
    comments = [{"at": _iso(first_touch), "author": ticket["assignee"].name, "text": "Wird bearbeitet." if ticket["language"] == "de" else "Looking into it."}]
    if resolved:
        comments.append({"at": _iso(resolved), "author": ticket["assignee"].name, "text": ticket["resolution"]})
    return {
        "ticket_id": ticket["ticket_id"], "queue": ticket["queue"], "subject": ticket["subject"], "description": ticket["description"],
        "priority": ticket["priority"], "status": _status_at(ticket, EXPORTED_AT), "language": ticket["language"], "classification": INTERNAL,
        "requester": {"employee_id": ticket["requester"].employee_id, "name": ticket["requester"].name, "email": ticket["requester"].email},
        "assignee": {"employee_id": ticket["assignee"].employee_id, "name": ticket["assignee"].name, "email": ticket["assignee"].email},
        "created_at": _iso(created), "resolved_at": _iso(resolved) if resolved else None,
        "related_incident": ticket["related_incident"], "comments": comments,
    }


def _ticket_exports(ctx: Context, tickets: list[dict]) -> None:
    header = ["ticket_id", "queue", "subject", "requester", "assignee", "priority", "status", "created_at", "resolved_at", "related_incident"]
    for year, quarter in [(year, q) for year in (2025, 2026) for q in (1, 2, 3, 4)][:7]:
        first = date(year, 3 * quarter - 2, 1)
        last = (date(year + 1, 1, 1) if quarter == 4 else date(year, 3 * quarter + 1, 1)) - timedelta(days=1)
        moment = min(_at(last, 23, 59), EXPORTED_AT)
        rows = [t for t in tickets if first <= t["created"].date() <= last]
        resolved = [_iso(t["resolved"]) if t["resolved"] and t["resolved"] <= moment else "" for t in rows]
        doc = ctx.store.add(Doc(
            doc_number=f"TCK-EXPORT-{year}-Q{quarter}", title=f"Ticket export {year}-Q{quarter}", doc_type="TICKET_EXPORT", fmt="csv",
            key=f"tickets/exports/tickets-{year}-q{quarter}.csv", label=INTERNAL, created_date=moment.date(),
            content=[header] + [[t["ticket_id"], t["queue"], t["subject"], t["requester"].name, t["assignee"].name, t["priority"],
                                 _status_at(t, moment), _iso(t["created"]), done, t["related_incident"] or ""] for t, done in zip(rows, resolved)],
        ))
        counts = Counter(t["requester"].name for t in rows).most_common(2)
        if counts and counts[0][1] >= 2 and (len(counts) == 1 or counts[0][1] > counts[1][1]):
            ctx.truth.offer_question(
                pool="comms:ticket-top-requester", category="analytics",
                question=f"According to the quarterly ticket export for {year}-Q{quarter}, which employee opened the most tickets?",
                answer=counts[0][0], sources=[ctx.truth.doc_source(doc)],
            )


def _tickets(ctx: Context) -> list[dict]:
    """Helpdesk and facilities tickets as individual JSON files plus one CSV export per quarter."""
    rng = ctx.rng("comms:tickets")
    tickets = sorted(_ticket_drafts(ctx, rng), key=lambda t: (t["created"], t["subject"]))
    sequence: Counter = Counter()
    incidents = {i["incident_id"]: i for i in ctx.facilities.incidents}
    for ticket in tickets:
        sequence[ticket["created"].year] += 1
        ticket["ticket_id"] = f"TCK-{ticket['created'].year}-{sequence[ticket['created'].year]:04d}"
        content = _ticket_json(ticket, rng)
        doc = ctx.store.add(Doc(
            doc_number=ticket["ticket_id"], title=ticket["subject"], doc_type="TICKET", fmt="json",
            key=f"tickets/{ticket['queue'].lower().replace('_', '-')}/{ticket['created'].year}/{ticket['ticket_id']}.json", label=INTERNAL,
            created_date=ticket["created"].date(), author_id=ticket["requester"].employee_id, author_name=ticket["requester"].name,
            language=ticket["language"], content=content,
        ))
        if ticket["related_incident"]:
            incident = incidents[ticket["related_incident"]]
            place = next((p for p in PLACES if p in incident["summary"]), None)
            if place:
                ctx.truth.offer_question(
                    pool="comms:ticket-incident", category="cross_source",
                    question=f"Where did the facility incident linked to ticket {ticket['ticket_id']} happen?",
                    answer=f"{place} ({incident['incident_id']})", must_include=[incident["incident_id"], place],
                    sources=[ctx.truth.doc_source(doc), ctx.truth.row_source("facility_incidents", incident["sensitivity"], incident_id=incident["incident_id"])],
                )
        elif rng.random() < 0.15:
            ctx.truth.offer_question(
                pool="comms:ticket-assignee", category="lookup",
                question=f"Who is assigned to ticket {ticket['ticket_id']}, and what is its status?",
                answer=f"{ticket['assignee'].name}; {content['status']}", must_include=[ticket["assignee"].name, content["status"]],
                sources=[ctx.truth.doc_source(doc)],
            )
    _ticket_exports(ctx, tickets)
    return tickets


def _backlog_mail(ctx: Context, mailer: _Mailer, tickets: list[dict]) -> None:
    rng = ctx.rng("comms:backlog")
    lead = _party(rng.choice(_people(ctx.personnel.active("CCS"), 10, 11)))
    for month in range(1, 10):
        day = _nth_weekday(2026, month, 0, 1)
        moment = _at(day, 8)
        backlog = sorted((t for t in tickets if t["created"] <= moment and (t["resolved"] is None or t["resolved"] > moment)), key=lambda t: t["created"])
        if len(backlog) < 2:
            continue
        oldest = backlog[0]
        rows = [["ticket_id", "queue", "subject", "requester", "assignee", "priority", "created_at"]]
        rows += [[t["ticket_id"], t["queue"], t["subject"], t["requester"].name, t["assignee"].name, t["priority"], _iso(t["created"])] for t in backlog]
        count = f"{len(backlog)} open tickets"
        mail = mailer.send(lead, [SERVICE_DESK], moment, f"Service desk backlog {day:%Y-%m}", _body(
            "Hello team,",
            f"attached is the service desk backlog as of {day.isoformat()}: {count}. The oldest is {oldest['ticket_id']}, opened on {oldest['created'].date().isoformat()}.",
            f"Regards,\n{lead.first}",
        ), attachment=(f"service-desk-backlog-{day:%Y-%m}.csv", _csv(rows)))
        ctx.truth.offer_question(
            pool="comms:backlog", category="lookup",
            question=f"How many tickets were open in the service desk backlog export sent on {day.isoformat()}, and which was the oldest?",
            answer=f"{count}; {oldest['ticket_id']}", must_include=[count, oldest["ticket_id"]], sources=[ctx.truth.doc_source(mail.doc)],
        )


# --------------------------------------------------------------------------
# Chat exports
# --------------------------------------------------------------------------

def _channel_members(ctx: Context, rng, channel: str) -> list[Employee]:
    active = ctx.personnel.active()
    if channel == "starhaven-integration":
        members = [ctx.person(h) for h in ("tarrow", "merriweather", "kalvane", "stroud", "sallow")] + rng.sample(_people(ctx.personnel.active("PMO"), 4, 11), 12)
    elif channel == "reactor-ops":
        members = [_reactor_engineer(ctx), ctx.person("kestrel")] + rng.sample(_people(ctx.personnel.active("RPS"), 3, 11), 16)
    elif channel == "procurement":
        members = [ctx.person("solberg")] + _people(ctx.personnel.active("SCM"), 1, 12)
    elif channel == "eriadu-werft":
        members = [ctx.person("brandt")] + rng.sample(_people(ctx.personnel.german_speakers(), 2, 11), 20)
    elif channel == "general":
        members = rng.sample(_people(active, 1, 12), 30)
    elif channel == "it-help":
        members = rng.sample(_people(ctx.personnel.active("CCS"), 2, 8), 8) + rng.sample(_people(active, 1, 12), 24)
    else:
        members = [ctx.person("valcourt")] + rng.sample(_people(ctx.personnel.active("SYD"), 3, 11), 18)
    return sorted({e.employee_id: e for e in members}.values(), key=lambda e: e.employee_id)


def _chat_line(ctx: Context, index: _Index, rng, channel: str, day: date) -> tuple[str, list[str]]:
    """A message and the replies it may get, drawn from what the channel talks about."""
    if channel == "starhaven-integration":
        zone = rng.choice(canon.ZONES)[0]
        comp = rng.choice([c for c in ctx.engineering.components if not c.planted_spec])
        return rng.choice([
            (f"{zone} is at {index.progress[(day, zone)]:.1f}% complete in today's progress report.", ["Thanks, noted for the weekly review."]),
            (f"Who has the approved revision of {comp.spec_number}?", [f"{comp.spec_number} Rev {comp.spec_revision} is the approved one; it is in the document registry."]),
            (f"Integration slot for the {comp.name.lower()} is confirmed for next week.", ["Great, I will let the test team know."]),
            ("Reminder: the program review is on Thursday at 09:00 in the Operations Centre conference suite.", []),
            (f"Crane time for {zone} is fully booked this week; please plan lifts with the yard first.", ["Understood."]),
        ])
    if channel == "reactor-ops":
        return rng.choice([
            (f"Shift handover: reactor output steady around {rng.randint(38, 44)}% rated.", ["Thanks, have a good evening."]),
            (f"Coolant manifold inspection on loop {rng.randint(1, 8)} complete, no findings.", []),
            (f"Containment field generator {rng.randint(1, 24)} is back online after scheduled maintenance.", ["Thanks for the update."]),
            (f"Heat exchanger stack {rng.randint(1, 32)} flushed and refilled.", []),
            ("Can someone check the trend on HR-CFG-F02? It looks noisy since this morning.", ["Looking at it now.", "Sensor lead was loose, fixed."]),
        ])
    if channel == "procurement":
        material = rng.choice(ctx.supply.materials)
        supplier = rng.choice(ctx.supply.suppliers)["name"]
        return rng.choice([
            (f"Anyone know the current lead time for {material['name']}?", [f"About {rng.randint(3, 16)} weeks from {supplier}."]),
            ("Supplier portal maintenance tonight from 22:00, please submit releases before then.", []),
            (f"Reminder: certificates of conformity are needed before goods receipt for {material['category'].lower()} items.", ["Noted."]),
            ("Month-end cut-off for purchase order releases is Friday at noon.", []),
        ])
    if channel == "eriadu-werft":
        hall = rng.randint(1, 6)
        options = [
            (f"Schicht {rng.choice('ABC')} beginnt heute um {rng.choice((6, 14, 22)):02d}:00 Uhr.", []),
            (f"Portalkran {rng.randint(1, 4)} ist bis {rng.randint(10, 15)}:00 Uhr außer Betrieb.", ["Danke für die Info."]),
            (f"Lieferung ist angekommen, liegt in Halle {hall}.", ["Super, wir holen sie nach der Pause."]),
            ("Wer hat den Messarm aus Halle 2?", ["Liegt bei der Qualitätssicherung."]),
            ("Nicht vergessen: Baubesprechung am Dienstag um 07:00 Uhr.", []),
        ]
        if STALL_START <= day <= STALL_END:
            options.append((f"Die Quadanium-Stahlträger für {STALLED_ZONE} sind immer noch nicht da.", ["Einkauf kümmert sich, die Bestellung ist eskaliert."]))
        return rng.choice(options)
    if channel == "general":
        return rng.choice([
            (f"The cafeteria on level {rng.randint(2, 60)} serves {rng.choice(('lentil stew', 'roasted vegetables', 'noodle soup', 'fresh greens from hydroponics'))} today.", []),
            (f"Tram band {rng.randint(1, 12)} is closed tonight for track work.", ["Thanks for the heads-up."]),
            ("Lost and found: a datapad was left in the conference suite.", ["That's mine, on my way!"]),
            ("Welcome to everyone who started this week!", ["Thank you!"]),
            ("The Eadu greenhouse tour still has a few places left.", ["Signed up."]),
        ])
    if channel == "it-help":
        return rng.choice([
            ("Is the mail system slow for anyone else?", ["Known issue, the team is on it.", "Fixed now."]),
            (f"The holo-projector in meeting room {rng.choice(ROOMS)} is not working.", ["Ticket raised."]),
            (f"Printer on floor {rng.randint(2, 60)} is jammed again.", ["On my way."]),
            ("My datapad calendar won't sync.", ["Please raise a ticket and we will reset the sync profile."]),
            ("How do I get a shared folder for my team?", ["Raise a ticket with the service desk."]),
        ])
    return rng.choice([
        (f"Slipway {rng.randint(1, 6)} keel blocks are set for the first hull.", ["Nice work."]),
        (f"Gantry crane {rng.randint(1, 8)} load test passed at {rng.choice((800, 1200, 2000, 3200))} t.", []),
        (f"Coating shop booth {rng.randint(1, 12)} cure cycle is running long today.", ["Thanks, we will shift the next job."]),
        (f"Outfitting quay berth {rng.randint(1, 14)} has shore power connected.", []),
    ])


def _planted_chat(ctx: Context, index: _Index, channel: str, first: date, last: date) -> list[tuple[datetime, Employee, str, list[tuple[Employee, str]]]]:
    """Messages that ground-truth questions ask about: the reactor peak and purchase orders sent to suppliers."""
    if channel == "reactor-ops" and first <= PEAK_AT.date() <= last:
        return [(PEAK_AT + timedelta(minutes=3), _reactor_engineer(ctx), f"{PEAK_SENSOR} just read {PEAK_VALUE} K. Checking the coolant loop now.",
                 [(ctx.person("kestrel"), "Thanks, keep me posted. Facilities is looking at the pump.")])]
    if channel == "procurement":
        orders = [po for po in ctx.supply.purchase_orders if first <= po["order_date"] <= last and po["status"] != "CANCELLED"][:4]
        return [(_at(po["order_date"], 15, 30) + timedelta(minutes=n), ctx.employee(po["requested_by"]),
                 f"{po['po_number']} sent to {index.suppliers[po['supplier_id']]['name']}.", []) for n, po in enumerate(orders)]
    return []


def _chat_export(ctx: Context, index: _Index, channel: str, language: str, month: date, members: list[Employee]) -> None:
    rng = ctx.rng(f"comms:chat:{channel}:{month:%Y-%m}")
    last = min((month + timedelta(days=32)).replace(day=1) - timedelta(days=1), AS_OF)
    present = [e for e in members if e.hire_date <= month]
    threads = []
    for _ in range(rng.randint(25, 50)):
        day = month + timedelta(days=rng.randint(0, (last - month).days))
        posted = _at(day, rng.randint(6, 19), rng.randrange(60)) + timedelta(seconds=rng.randrange(60))
        author = rng.choice(present)
        text, answers = _chat_line(ctx, index, rng, channel, day)
        replies = [(rng.choice([e for e in present if e is not author]), answer) for answer in answers if rng.random() < 0.7]
        threads.append((posted, author, text, replies))
    planted = _planted_chat(ctx, index, channel, month, last)
    threads += planted
    threads.sort(key=lambda thread: (thread[0], thread[1].employee_id))
    messages, posters = [], Counter()
    for n, (posted, author, text, replies) in enumerate(threads, start=1):
        message_id = f"{channel}-{month:%Y%m}-{n:04d}"
        posters[author.name] += 1
        thread = []
        for r, (replier, answer) in enumerate(replies, start=1):
            posters[replier.name] += 1
            thread.append({"id": f"{message_id}-r{r}", "ts": _iso(posted + timedelta(minutes=4 * r + rng.randint(0, 3))),
                           "user_id": replier.employee_id, "user": replier.name, "text": answer})
        messages.append({"id": message_id, "ts": _iso(posted), "user_id": author.employee_id, "user": author.name, "text": text, "replies": thread})
    count = sum(posters.values())
    doc = ctx.store.add(Doc(
        doc_number=f"CHAT-{channel}-{month:%Y-%m}", title=f"#{channel} chat export, {month:%Y-%m}", doc_type="CHAT_EXPORT", fmt="json",
        key=f"chat/{channel}/{month:%Y-%m}.json", label=INTERNAL, created_date=last, language=language,
        content={
            "export": {"workspace": canon.COMPANY, "channel": f"#{channel}", "month": f"{month:%Y-%m}", "language": language,
                       "classification": INTERNAL, "exported_at": _iso(EXPORTED_AT), "message_count": count},
            "members": [{"user_id": e.employee_id, "name": e.name, "title": e.title} for e in present],
            "messages": messages,
        },
    ))
    source = ctx.truth.doc_source(doc)
    ctx.truth.offer_question(
        pool="comms:chat-count", category="analytics",
        question=f"How many messages, including thread replies, were posted in #{channel} in {month:%B %Y}?",
        answer=str(count), sources=[source],
    )
    top = posters.most_common(2)
    if len(top) == 2 and top[0][1] > top[1][1]:
        ctx.truth.offer_question(
            pool="comms:chat-top-poster", category="analytics",
            question=f"Who posted the most messages, including thread replies, in #{channel} in {month:%B %Y}?",
            answer=top[0][0], sources=[source],
        )
    for posted, author, text, _ in planted:
        if channel == "reactor-ops":
            question = f"Who first reported the {PEAK_SENSOR} reading in #reactor-ops on {posted.date().isoformat()}?"
            pool = "comms:chat-reactor"
        else:
            question = f"In #procurement, who posted that {text.rstrip('.')}?"
            pool = "comms:chat-po"
        ctx.truth.offer_question(pool=pool, category="lookup", question=question, answer=author.name, sources=[source])


def _chat(ctx: Context, index: _Index) -> None:
    rng = ctx.rng("comms:chat-members")
    for channel, language, first_month in CHANNELS:
        members = _channel_members(ctx, rng, channel)
        for month in range(first_month, AS_OF.month + 1):
            _chat_export(ctx, index, channel, language, date(AS_OF.year, month, 1), members)


# --------------------------------------------------------------------------
# Calendar invites
# --------------------------------------------------------------------------

@dataclass
class _Calendar:
    """Writes one meeting invite per .ics document."""

    ctx: Context
    count: int = 0

    def invite(self, start: datetime, minutes: int, summary: str, location: str, description: str, organizer: Party,
               attendees: list[Party], label: str = INTERNAL, language: str = "en") -> Doc:
        self.count += 1
        uid = f"evt-{self.count:05d}"
        lines = [
            "BEGIN:VCALENDAR", f"PRODID:-//{canon.COMPANY}//Calendar//EN", "VERSION:2.0", "CALSCALE:GREGORIAN", "METHOD:REQUEST",
            "BEGIN:VEVENT", f"UID:{uid}@{EMPIRE_DOMAIN}", f"DTSTAMP:{EXPORTED_AT:%Y%m%dT%H%M%SZ}",
            f"DTSTART:{start:%Y%m%dT%H%M%SZ}", f"DTEND:{start + timedelta(minutes=minutes):%Y%m%dT%H%M%SZ}",
            f"SUMMARY:{ics_text(summary)}", f"LOCATION:{ics_text(location)}", f"DESCRIPTION:{ics_text(description)}",
            f'ORGANIZER;CN="{organizer.name}":mailto:{organizer.email}',
            *[f'ATTENDEE;CN="{p.name}";ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{p.email}' for p in attendees],
            f"X-EMPIRE-CLASSIFICATION:{label}", "END:VEVENT", "END:VCALENDAR",
        ]
        return self.ctx.store.add(Doc(
            doc_number=uid.upper(), title=summary, doc_type="CALENDAR_INVITE", fmt="ics", key=f"calendar/{start:%Y}/{start:%m}/{uid}.ics",
            label=label, created_date=start.date(), author_id=organizer.employee_id, author_name=organizer.name, language=language,
            content="".join(ics_fold(line) + "\r\n" for line in lines),
        ))


def _weekly_days(first: date, step_weeks: int, skip: tuple[date, ...]) -> list[date]:
    days, day = [], first
    while day <= AS_OF:
        if day not in skip:
            days.append(day)
        day += timedelta(weeks=step_weeks)
    return days


def _program_reviews(ctx: Context, calendar: _Calendar) -> None:
    rps_change = next(start for dept, _, start, _ in canon.DEPARTMENT_HEADS if dept == "RPS" and start > WINDOW_START)
    director_change = next(start for program, _, role, start, _ in canon.PROGRAM_ROLES
                           if program == canon.MAIN_PROGRAM and role == "PROGRAM_DIRECTOR" and start > WINDOW_START)
    for day in _weekly_days(_nth_weekday(2026, 1, 3, 1), 1, REVIEW_SKIP):
        chair_row = leader_row(ctx, "PROGRAM", canon.MAIN_PROGRAM, "PROGRAM_DIRECTOR", day)
        chair = ctx.employee(chair_row["employee_id"])
        invited = [ctx.person("kalvane"), ctx.person("stroud")] + [ctx.head_of(dept, day) for dept in ("RPS", "STR", "CON", "QAT", "SCM")]
        attendees = list({e.employee_id: _party(e) for e in invited if e.employee_id != chair.employee_id}.values())
        doc = calendar.invite(_at(day, 9), 90, f"{canon.STATION} weekly program review", "Operations Centre conference suite",
                              f"Weekly program review, {day.isoformat()}. Agenda: work package status, decisions, risks and issues, action items.",
                              _party(chair), attendees)
        if abs((day - director_change).days) <= 21:
            ctx.truth.offer_question(
                pool="comms:review-organizer", category="temporal",
                question=f"Who organized the {canon.STATION} weekly program review on {day.isoformat()}?",
                answer=chair.name, sources=[ctx.truth.doc_source(doc), leadership_source(ctx, chair_row)],
            )
        if abs((day - rps_change).days) <= 28:
            row = leader_row(ctx, "DEPARTMENT", canon.DEPT_ID["RPS"], "HEAD", day)
            ctx.truth.offer_question(
                pool="comms:review-attendee", category="temporal",
                question=f"Who attended the {canon.STATION} weekly program review on {day.isoformat()} as head of {canon.DEPT_NAME['RPS']}?",
                answer=ctx.name(row["employee_id"]), sources=[ctx.truth.doc_source(doc), leadership_source(ctx, row)],
            )


def _recurring_invites(ctx: Context, calendar: _Calendar, index: _Index) -> None:
    rng = ctx.rng("comms:calendar")
    brandt = _party(ctx.person("brandt"))
    for day in _weekly_days(_nth_weekday(2026, 1, 1, 1), 2, ERIADU_SKIP):
        calendar.invite(_at(day, 7), 60, f"Baubesprechung {canon.GERMAN_SITE_DE}", f"{canon.GERMAN_SITE_DE}, Besprechungsraum Halle 1",
                        f"Baubesprechung am {de_date(day)}. Tagesordnung: Arbeitssicherheit, Stand der Fertigung, Materiallage, Maßnahmen.",
                        brandt, [ERIADU_TEAM], language="de")

    solberg = _party(ctx.person("solberg"))
    danvik = _supplier_party(index.suppliers[KDY["supplier_id"]])
    buyers = _people(ctx.personnel.active("SCM"), 6, 9)
    structures = _people(ctx.personnel.active("STR"), 10, 11)
    for month in range(1, AS_OF.month + 1):
        day = _nth_weekday(2026, month, 2, 1)
        doc = calendar.invite(_at(day, 13), 60, "Kuat Drive Yards monthly supplier review", f"{canon.HQ}, room H41-12, with HoloNet link",
                              f"Monthly supplier review, {day.isoformat()}: contract {KDY['contract_id']} ({KDY['contract_title']}), open purchase orders, delivery schedule and quality notes.",
                              solberg, [danvik, _party(rng.choice(buyers)), _party(rng.choice(structures))])
        if month in (3, 6, 9):
            ctx.truth.offer_question(
                pool="comms:kdy-review", category="lookup",
                question=f"Which Kuat Drive Yards representative is invited to the monthly supplier review on {day.isoformat()}?",
                answer=danvik.name, sources=[ctx.truth.doc_source(doc)],
            )

    for month in (1, 4, 7):
        day = _nth_weekday(2026, month, 3, 3)
        host = ctx.head_of("OCH", day)
        doc = calendar.invite(_at(day, 15), 60, f"{canon.COMPANY} quarterly all-hands", f"{canon.HQ} auditorium and HoloNet stream",
                              f"Quarterly all-hands, {day.isoformat()}, hosted by {host.name}. Questions can be sent in advance to the Office of the Chairman.",
                              _party(host), [ALL_STAFF])
        ctx.truth.offer_question(
            pool="comms:all-hands", category="lookup",
            question=f"Who hosts the {canon.COMPANY} quarterly all-hands meeting on {day.isoformat()}?",
            answer=host.name, sources=[ctx.truth.doc_source(doc)],
        )


def _team_meetings(ctx: Context, calendar: _Calendar) -> None:
    rng = ctx.rng("comms:team-meetings")
    for dept in ("RPS", "AGR"):
        for month in range(1, AS_OF.month + 1):
            day = _nth_weekday(2026, month, 1, 2)
            row = leader_row(ctx, "DEPARTMENT", canon.DEPT_ID[dept], "HEAD", day)
            organizer = ctx.employee(row["employee_id"])
            team = [e for e in ctx.personnel.active(dept) if e.hire_date <= day and e.employee_id != organizer.employee_id]
            summary = f"{canon.DEPT_NAME[dept]} monthly team meeting"
            doc = calendar.invite(_at(day, 14), 60, summary, f"{canon.HQ}, room H41-07",
                                  f"Monthly team meeting, {day.isoformat()}. Agenda: priorities, staffing, open issues.",
                                  _party(organizer), [_party(e) for e in rng.sample(team, min(6, len(team)))])
            ctx.truth.offer_question(
                pool="comms:team-meeting-organizer", category="temporal",
                question=f"Who organized the {summary} on {day.isoformat()}?",
                answer=organizer.name, sources=[ctx.truth.doc_source(doc), leadership_source(ctx, row)],
            )

    others = [code for _, code, _, _ in canon.DEPARTMENTS if code not in ("RPS", "AGR", "OCH")]
    for n in range(30):
        dept = others[n % len(others)]
        day = _weekday(WINDOW_START + timedelta(days=rng.randint(4, (AS_OF - WINDOW_START).days - 3)))
        organizer = ctx.head_of(dept, day)
        team = [e for e in ctx.personnel.active(dept) if e.hire_date <= day and e.employee_id != organizer.employee_id]
        label = INTERNAL
        if dept == "FIN":
            summary, description, label = f"Quarterly budget review Q{(day.month - 1) // 3 + 1} {day.year}", "Budget against actuals per program; forecast changes.", CONFIDENTIAL
        elif dept == "FAC":
            summary, description = "Workplace safety refresher", "Annual refresher: evacuation routes, first aid, reporting near misses."
        else:
            summary, description = f"{canon.DEPT_NAME[dept]} team meeting", "Agenda: priorities, staffing, open issues."
        calendar.invite(_at(day, rng.choice((10, 11, 14, 15))), 60, summary, f"{canon.HQ}, room H41-{rng.randint(1, 20):02d}",
                        f"{description} Date: {day.isoformat()}.", _party(organizer),
                        [_party(e) for e in rng.sample(team, min(rng.randint(4, 8), len(team)))], label=label)


# --------------------------------------------------------------------------
# Questions with no answer in the dataset
# --------------------------------------------------------------------------

def _no_answer(ctx: Context) -> None:
    po_numbers = {po["po_number"] for po in ctx.supply.purchase_orders}
    missing_po = next(f"EI-PO-2026-{n:05d}" for n in range(9999, 0, -1) if f"EI-PO-2026-{n:05d}" not in po_numbers)
    for question in (
        f"Which delivery date did Kuat Drive Yards confirm for purchase order {missing_po}?",
        f"Who organized the {canon.STATION} weekly program review on 2026-08-15?",
        "Which helpdesk ticket reported a broken holo-projector at the Eadu greenhouse hall in 2024?",
        "What was agreed at the Kuat Drive Yards supplier review in December 2025?",
        f"Who announced a change of head of {canon.DEPT_NAME['SYD']} in 2026?",
        "What was discussed in the #starhaven-integration chat channel in October 2026?",
    ):
        ctx.truth.offer_question(pool="comms:no-answer", category="no_answer", question=question, answer=None, sources=[], expected_type="not_found")


def build(ctx: Context) -> None:
    index = _index(ctx)
    ncrs = [d for d in ctx.store.docs if d.doc_type == "NONCONFORMANCE_REPORT"]
    tests = [d for d in ctx.store.docs if d.doc_type == "TEST_REPORT"]
    mailer = _Mailer(ctx)
    tickets = _tickets(ctx)
    _announcements(ctx, mailer)
    _kdy_mail(ctx, mailer, index)
    _supplier_mail(ctx, mailer, index)
    _beam_shortage(ctx, mailer, index)
    _reactor_peak(ctx, mailer)
    _ncr_followups(ctx, mailer, ncrs)
    _test_followups(ctx, mailer, tests)
    _farewells(ctx, mailer)
    _welcomes(ctx, mailer)
    _work_package_mail(ctx, mailer)
    _spec_reviews(ctx, mailer)
    _po_approvals(ctx, mailer, index)
    _notices(ctx, mailer)
    _eriadu_mail(ctx, mailer, index)
    _backlog_mail(ctx, mailer, tickets)
    _sender_departments(ctx, mailer.sent)
    _chat(ctx, index)
    calendar = _Calendar(ctx)
    _program_reviews(ctx, calendar)
    _recurring_invites(ctx, calendar, index)
    _team_meetings(ctx, calendar)
    _no_answer(ctx)
