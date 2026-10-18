"""Email and calendar building blocks with deterministic output."""

from datetime import datetime
from email.message import EmailMessage
from email.utils import format_datetime


def email_message(sender: str, sender_name: str, recipients: list[str], subject: str, sent: datetime, body: str,
                  message_id: str, label: str) -> EmailMessage:
    """A plain-text email; the Message-ID uses the sender's domain."""
    message = EmailMessage()
    message["From"] = f"{sender_name} <{sender}>"
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message["Date"] = format_datetime(sent)
    message["Message-ID"] = f"<{message_id}@{sender.split('@')[1]}>"
    message["X-Classification"] = label
    message.set_content(body)
    return message


def ics_text(value: str) -> str:
    """Escape a TEXT value for iCalendar (RFC 5545, section 3.3.11)."""
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics_fold(line: str) -> str:
    """Fold a content line at 75 octets (RFC 5545, section 3.1).

    Lines break before a ";", ":" or space where possible, so names and
    addresses stay whole for readers that do not unfold.
    """
    parts: list[str] = []
    while len(line.encode()) > (74 if parts else 75):
        fit = len(line.encode()[:74 if parts else 75].decode("utf-8", "ignore"))
        cut = max(line.rfind(delimiter, 1, fit) for delimiter in (";", ":", " "))
        cut = cut if cut > 0 else fit
        parts.append(line[:cut])
        line = line[cut:]
    parts.append(line)
    return "\r\n ".join(parts)


def ics_calendar(lines: list[str]) -> str:
    """Join content lines into an iCalendar object with folded lines and CRLF endings."""
    return "".join(ics_fold(line) + "\r\n" for line in lines)
