"""What an agent's SQL may read in each tenant database, with or without pseudonyms.

Two schemas of views over each tenant's tables, with the same view names and
the same columns, so an agent's tools look identical whichever it gets:

- `agent_raw`: the values as they are (the control loop).
- `agent`: every personal value replaced by a pseudonym (the scrubbing loops):
  a person's name, email, badge, home address, comlink, emergency contact,
  salary, review rating and salary increase. Names inside free text
  (document titles, history notes) are swapped for the same pseudonyms.

In both, `employees` shows one `name` column in place of `first_name` and
`last_name`, so a name and its pseudonym are the same thing.

**A pseudonym** is `<KIND>_` and the first ten hex digits of
HMAC-SHA256(key, normalized value). A text value is normalized by trimming,
collapsing whitespace to one space, NFC and lower case; a number by its
digits alone, without separators or trailing zeros. The same value gets the
same pseudonym in every row, every table and every run with the same key, so
a scrubber outside the database that follows `pseudonym` here produces the
pseudonyms the views show.

**A role per variant and access level** (`<tenant>_<raw|scrubbed>_<level>`)
connects only to its tenant's database and reads only its own schema, and
only the rows whose label is at or below its level. The pseudonym key and the
role-to-level table live in `agent_private`, which no agent role can read.

**Summaries** (`salary_summary`, `review_summary`) are the only way to
salaries and ratings in aggregate: fixed groupings, groups of at least
`MIN_GROUP` people, averages rounded. Their rows are Confidential.
"""

import hashlib
import hmac
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from generator.database import Table
from generator.labels import CONFIDENTIAL, LABELS, RANK

VARIANTS = {"raw": "agent_raw", "scrubbed": "agent"}
"""Variant → the schema its roles read."""
PRIVATE = "agent_private"
DEFAULT_KEY = "empire-local-pseudonym-key"
"""The key `docker compose` uses unless `PSEUDONYM_KEY` is set: local test data only."""
PSEUDONYM_DIGITS = 10
NUMERIC_KINDS = ("SALARY", "RATING", "PERCENT")
GRADE_BANDS = ((1, 3), (4, 6), (7, 9), (10, 12), (13, 15))
MIN_GROUP = 5


@dataclass(frozen=True)
class Personal:
    """A view column holding a personal value: its kind and how it is made from the base row `t`."""

    column: str
    kind: str
    expression: str
    replaces: tuple[str, ...] = ()
    """Base columns the view leaves out because this one stands for them."""


@dataclass(frozen=True)
class TenantAccess:
    tenant: str
    database: str
    schema: str
    personal: Mapping[str, tuple[Personal, ...]]
    free_text: Mapping[str, tuple[str, ...]]
    """Table → text columns whose people's names are swapped for pseudonyms."""
    names: str
    """SQL listing every name to swap in free text, one per row."""


def _person(prefix: str = "") -> Personal:
    return Personal("name", "PERSON", f"t.{prefix}first_name || ' ' || t.{prefix}last_name", ("first_name", "last_name"))


EMPIRE = TenantAccess(
    tenant="empire",
    database="empire_inc",
    schema="empire",
    personal={
        "employees": (_person(), Personal("email", "EMAIL", "t.email"), Personal("badge_number", "BADGE", "t.badge_number")),
        "employee_private": (
            Personal("salary_credits", "SALARY", "t.salary_credits"),
            Personal("home_address", "ADDRESS", "t.home_address"),
            Personal("personal_comlink", "PHONE", "t.personal_comlink"),
            Personal("emergency_contact", "CONTACT", "t.emergency_contact"),
        ),
        "compensation_history": (Personal("salary_credits", "SALARY", "t.salary_credits"),),
        "performance_reviews": (
            Personal("rating", "RATING", "t.rating"),
            Personal("rating_label", "REVIEW", "t.rating_label"),
            Personal("salary_increase_pct", "PERCENT", "t.salary_increase_pct"),
        ),
        "suppliers": (Personal("contact_name", "PERSON", "t.contact_name"), Personal("contact_email", "EMAIL", "t.contact_email")),
    },
    free_text={"documents": ("title",), "employment_history": ("note",)},
    names="SELECT first_name || ' ' || last_name FROM empire.employees UNION SELECT contact_name FROM empire.suppliers",
)

KDY = TenantAccess(
    tenant="kdy",
    database="kdy",
    schema="kdy",
    personal={
        "employees": (_person(), Personal("email", "EMAIL", "t.email")),
        "employee_private": (
            Personal("salary_credits", "SALARY", "t.salary_credits"),
            Personal("home_address", "ADDRESS", "t.home_address"),
            Personal("personal_comlink", "PHONE", "t.personal_comlink"),
        ),
    },
    free_text={"documents": ("title",)},
    names="SELECT first_name || ' ' || last_name FROM kdy.employees",
)
TENANTS = {access.tenant: access for access in (EMPIRE, KDY)}


def role(tenant: str, variant: str, level: str) -> str:
    return f"{tenant}_{variant}_{level.lower()}"


def password(role_name: str) -> str:
    """A role's password: these roles exist only in the local test database."""
    return f"{role_name}-local-only"


def roles(tenant: str) -> list[tuple[str, str, str]]:
    """(role, variant, level) for every role of a tenant."""
    return [(role(tenant, variant, level), variant, level) for variant in VARIANTS for level in LABELS]


# --------------------------------------------------------------------------
# Pseudonyms: the reference implementation the views follow
# --------------------------------------------------------------------------

def normalized(kind: str, value: object) -> str:
    text = str(value)
    if kind in NUMERIC_KINDS:
        number = Decimal(re.sub(r"[^0-9.\-]", "", text)).normalize()
        return format(number, "f")
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", text.strip())).lower()


def pseudonym(kind: str, value: object, key: bytes) -> str:
    digest = hmac.new(key, normalized(kind, value).encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{kind}_{digest[:PSEUDONYM_DIGITS]}"


# --------------------------------------------------------------------------
# Summaries: the rule both the views and the expected answers follow
# --------------------------------------------------------------------------

def grade_band(grade: object) -> str:
    value = int(grade)
    return next(f"{low}-{high}" for low, high in GRADE_BANDS if low <= value <= high)


def _rounded(total: Decimal, count: int, places: str) -> Decimal:
    return (total / count).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def salary_summary(employees: Iterable[Mapping], private: Iterable[Mapping], departments: Iterable[Mapping]) -> list[dict]:
    """Active employees by department and grade band: headcount and average
    salary to the nearest 1,000 credits, groups of `MIN_GROUP` or more."""
    salary = {row["employee_id"]: Decimal(str(row["salary_credits"])) for row in private}
    names = {row["department_id"]: row["name"] for row in departments}
    groups: dict[tuple[str, str], list[Decimal]] = {}
    for row in employees:
        if row["status"] == "ACTIVE":
            groups.setdefault((names[row["department_id"]], grade_band(row["grade"])), []).append(salary[row["employee_id"]])
    return [
        {"department": department, "grade_band": band, "headcount": len(values),
         "average_salary_credits": str(_rounded(sum(values), len(values), "1E3").quantize(Decimal(1))), "sensitivity": CONFIDENTIAL}
        for (department, band), values in sorted(groups.items()) if len(values) >= MIN_GROUP
    ]


def review_summary(employees: Iterable[Mapping], reviews: Iterable[Mapping], departments: Iterable[Mapping]) -> list[dict]:
    """Reviews by the employee's department and cycle: count, average rating
    (two places) and average salary increase (one place), groups of
    `MIN_GROUP` or more."""
    department_of = {row["employee_id"]: row["department_id"] for row in employees}
    names = {row["department_id"]: row["name"] for row in departments}
    groups: dict[tuple[str, int], list[tuple[Decimal, Decimal]]] = {}
    for row in reviews:
        key = (names[department_of[row["employee_id"]]], int(row["cycle_year"]))
        groups.setdefault(key, []).append((Decimal(str(row["rating"])), Decimal(str(row["salary_increase_pct"]))))
    return [
        {"department": department, "cycle_year": year, "reviews": len(values),
         "average_rating": str(_rounded(sum(r for r, _ in values), len(values), "0.01")),
         "average_salary_increase_pct": str(_rounded(sum(p for _, p in values), len(values), "0.1")),
         "sensitivity": CONFIDENTIAL}
        for (department, year), values in sorted(groups.items()) if len(values) >= MIN_GROUP
    ]


SUMMARIES = {"salary_summary": (salary_summary, "employee_private"), "review_summary": (review_summary, "performance_reviews")}
"""Each summary view → its rule here and the table it reads besides employees and departments."""


# --------------------------------------------------------------------------
# SQL
# --------------------------------------------------------------------------

def _literal(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _visible(alias: str) -> str:
    """Rows whose label the connected role may see. Views read `agent_private`
    with their owner's rights, so no agent role needs any right there."""
    return (
        f"(SELECT rank FROM {PRIVATE}.label_ranks WHERE label = {alias}.sensitivity) <= "
        f"(SELECT r.rank FROM {PRIVATE}.role_levels l JOIN {PRIVATE}.label_ranks r USING (label) "
        "WHERE l.role_name = current_user)"
    )


def _columns(access: TenantAccess, table: Table, scrubbed: bool) -> list[str]:
    """The view's select list over the base row `t`, in the table's own column order."""
    personal = {p.replaces[0] if p.replaces else p.column: p for p in access.personal.get(table.name, ())}
    dropped = {name for p in personal.values() for name in p.replaces[1:]}
    out = []
    for column in table.columns:
        if column.name in dropped:
            continue
        if column.name in personal:
            p = personal[column.name]
            out.append(f"{PRIVATE}.pseudonym('{p.kind}', ({p.expression})::text) AS {p.column}" if scrubbed else f"{p.expression} AS {p.column}")
        elif scrubbed and column.name in access.free_text.get(table.name, ()):
            out.append(f"{PRIVATE}.scrub_names(t.{column.name}) AS {column.name}")
        else:
            out.append(f"t.{column.name}")
    return out + ["t.sensitivity"]


def _summaries(access: TenantAccess, schema: str) -> list[str]:
    if access.tenant != "empire":
        return []
    base = access.schema
    bands = " ".join(f"WHEN e.grade BETWEEN {low} AND {high} THEN '{low}-{high}'" for low, high in GRADE_BANDS)
    return [
        f"""CREATE VIEW {schema}.salary_summary WITH (security_barrier) AS
SELECT * FROM (
  SELECT d.name AS department, CASE {bands} END AS grade_band, count(*) AS headcount,
         round(avg(p.salary_credits), -3) AS average_salary_credits, '{CONFIDENTIAL}'::text AS sensitivity
  FROM {base}.employees e JOIN {base}.employee_private p USING (employee_id) JOIN {base}.departments d USING (department_id)
  WHERE e.status = 'ACTIVE' GROUP BY 1, 2 HAVING count(*) >= {MIN_GROUP}
) t WHERE {_visible('t')};
COMMENT ON VIEW {schema}.salary_summary IS 'Active employees by department and grade band: headcount and average salary in credits, rounded to 1,000. Only groups of {MIN_GROUP} or more.';""",
        f"""CREATE VIEW {schema}.review_summary WITH (security_barrier) AS
SELECT * FROM (
  SELECT d.name AS department, r.cycle_year, count(*) AS reviews, round(avg(r.rating), 2) AS average_rating,
         round(avg(r.salary_increase_pct), 1) AS average_salary_increase_pct, '{CONFIDENTIAL}'::text AS sensitivity
  FROM {base}.performance_reviews r JOIN {base}.employees e USING (employee_id) JOIN {base}.departments d USING (department_id)
  GROUP BY 1, 2 HAVING count(*) >= {MIN_GROUP}
) t WHERE {_visible('t')};
COMMENT ON VIEW {schema}.review_summary IS 'Performance reviews by department and cycle year: count, average rating (1-5) and average salary increase in percent. Only groups of {MIN_GROUP} or more.';""",
    ]


def access_sql(access: TenantAccess, tables: Sequence[Table]) -> str:
    private = PRIVATE
    lines = [
        "-- Generated by `python -m generator`. Do not edit by hand.",
        f"-- The agent's views of {access.database}: `{VARIANTS['raw']}` (values as they are) and",
        f"-- `{VARIANTS['scrubbed']}` (personal values as pseudonyms), and one role per variant and level.",
        "-- Run as the database owner after load.sql: psql -v pseudonym_key=<key> -f agent_access.sql",
        "\\set ON_ERROR_STOP on",
        "SET client_min_messages = warning;",
        "BEGIN;",
        "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
        f"DROP SCHEMA IF EXISTS {VARIANTS['raw']}, {VARIANTS['scrubbed']}, {private} CASCADE;",
        f"CREATE SCHEMA {private};",
        "REVOKE ALL ON SCHEMA public FROM PUBLIC;",
        f"CREATE TABLE {private}.pseudonym_key (key bytea NOT NULL);",
        f"INSERT INTO {private}.pseudonym_key VALUES (convert_to(:'pseudonym_key', 'UTF8'));",
        f"CREATE TABLE {private}.label_ranks (label text PRIMARY KEY, rank integer NOT NULL);",
        f"INSERT INTO {private}.label_ranks VALUES " + ", ".join(f"('{label}', {RANK[label]})" for label in LABELS) + ";",
        f"CREATE TABLE {private}.role_levels (role_name text PRIMARY KEY, label text NOT NULL REFERENCES {private}.label_ranks);",
        f"""CREATE FUNCTION {private}.normalized(kind text, value text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT CASE WHEN kind IN ({', '.join(_literal(k) for k in NUMERIC_KINDS)})
    THEN trim_scale(regexp_replace(value, '[^0-9.-]', '', 'g')::numeric)::text
    ELSE lower(normalize(regexp_replace(regexp_replace(value, '\\s+', ' ', 'g'), '^ | $', '', 'g'), NFC)) END
$$;""",
        f"""CREATE FUNCTION {private}.pseudonym(kind text, value text) RETURNS text LANGUAGE sql STABLE AS $$
  SELECT CASE WHEN value IS NULL THEN NULL ELSE kind || '_' || left(encode(hmac(convert_to({private}.normalized(kind, value), 'UTF8'),
    (SELECT key FROM {private}.pseudonym_key), 'sha256'), 'hex'), {PSEUDONYM_DIGITS}) END
$$;""",
        f"CREATE TABLE {private}.known_names AS SELECT n AS name, {private}.pseudonym('PERSON', n) AS pseudonym FROM ({access.names}) names(n) WHERE n IS NOT NULL;",
        f"""CREATE FUNCTION {private}.scrub_names(value text) RETURNS text LANGUAGE plpgsql STABLE AS $$
DECLARE known record;
BEGIN
  IF value IS NULL THEN RETURN NULL; END IF;
  FOR known IN SELECT name, pseudonym FROM {private}.known_names ORDER BY length(name) DESC, name LOOP
    IF strpos(value, known.name) > 0 THEN value := replace(value, known.name, known.pseudonym); END IF;
  END LOOP;
  RETURN value;
END $$;""",
        f"REVOKE ALL ON ALL FUNCTIONS IN SCHEMA {private} FROM PUBLIC;",
    ]
    for variant, schema in VARIANTS.items():
        scrubbed = variant == "scrubbed"
        lines.append(f"CREATE SCHEMA {schema};")
        for table in tables:
            changes = table.name in access.personal or (scrubbed and table.name in access.free_text)
            select = ", ".join(_columns(access, table, scrubbed))
            source = f"{access.schema}.{table.name}"
            if scrubbed and changes:
                # Pseudonyms are worked out once, by the owner, and kept: no agent role ever runs the key.
                lines.append(f"CREATE MATERIALIZED VIEW {private}.{table.name} AS SELECT {select} FROM {source} t;")
                lines.append(f"CREATE VIEW {schema}.{table.name} WITH (security_barrier) AS SELECT * FROM {private}.{table.name} t WHERE {_visible('t')};")
            else:
                lines.append(f"CREATE VIEW {schema}.{table.name} WITH (security_barrier) AS SELECT {select} FROM {source} t WHERE {_visible('t')};")
            note = " Personal values are pseudonyms (KIND_hex): the same value always has the same one." if scrubbed and changes else ""
            lines.append(f"COMMENT ON VIEW {schema}.{table.name} IS {_literal(table.comment + note)};")
        lines += _summaries(access, schema)
    for name, variant, level in roles(access.tenant):
        lines += [
            f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{name}') THEN CREATE ROLE {name} LOGIN; END IF; END $$;",
            f"ALTER ROLE {name} LOGIN PASSWORD {_literal(password(name))} NOSUPERUSER NOCREATEDB NOCREATEROLE;",
            f"ALTER ROLE {name} IN DATABASE {access.database} SET search_path = {VARIANTS[variant]};",
            f"ALTER ROLE {name} IN DATABASE {access.database} SET default_transaction_read_only = on;",
            f"GRANT USAGE ON SCHEMA {VARIANTS[variant]} TO {name};",
            f"GRANT SELECT ON ALL TABLES IN SCHEMA {VARIANTS[variant]} TO {name};",
            f"INSERT INTO {private}.role_levels VALUES ('{name}', '{level}');",
        ]
    lines += [
        f"""DO $$ BEGIN
  EXECUTE format('REVOKE ALL ON DATABASE %I FROM PUBLIC', current_database());
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO {", ".join(name for name, _, _ in roles(access.tenant))}', current_database());
END $$;""",
        "COMMIT;",
    ]
    return "\n".join(lines) + "\n"


def write(out_dir: Path, access: TenantAccess, tables: Sequence[Table]) -> None:
    (out_dir / "agent_access.sql").write_text(access_sql(access, tables), encoding="utf-8")


def login_roles(tenant: str) -> dict[str, dict[str, str]]:
    """Per access level, the role each variant connects as, for `logins.json`."""
    return {level: {variant: role(tenant, variant, level) for variant in VARIANTS} for level in LABELS}
