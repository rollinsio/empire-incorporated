"""The agent's views: pseudonyms that match the reference, no personal value in the clear,
and roles that see only their own schema and level.

The first tests read the generated `agent_access.sql` and the reference
implementation. The rest connect to a database loaded by `db/load.sh` (the
local `docker compose` stack, `EMPIRE_DATABASE_HOST`/`EMPIRE_DATABASE_PORT`,
default localhost:55432) as the agent roles, and are skipped without one.
"""

import os
import re

import pytest

from generator import agent_access as access
from generator.labels import LABELS

HOST = os.environ.get("EMPIRE_DATABASE_HOST", "localhost")
PORT = int(os.environ.get("EMPIRE_DATABASE_PORT", "55432"))
KEY = os.environ.get("PSEUDONYM_KEY", access.DEFAULT_KEY).encode()


# -- the reference pseudonyms ----------------------------------------------------------------


def test_a_pseudonym_is_its_kind_and_ten_hex_digits_and_ignores_spelling_noise() -> None:
    one = access.pseudonym("PERSON", "Mira Kestrel", KEY)
    assert re.fullmatch(r"PERSON_[0-9a-f]{10}", one)
    assert access.pseudonym("PERSON", "  mira\tKESTREL ", KEY) == one
    assert access.pseudonym("EMAIL", "Mira Kestrel", KEY) == one.replace("PERSON", "EMAIL"), "the kind only labels it"
    assert access.pseudonym("PERSON", "Mira Kestrel", b"another key") != one
    assert access.pseudonym("SALARY", "110,700", KEY) == access.pseudonym("SALARY", "110700", KEY)
    assert access.pseudonym("PERCENT", "4.0", KEY) == access.pseudonym("PERCENT", "4", KEY)


# -- the generated SQL ------------------------------------------------------------------------


@pytest.fixture(scope="module", params=sorted(access.TENANTS))
def tenant_sql(request, dataset) -> tuple[access.TenantAccess, str]:
    return access.TENANTS[request.param], (dataset.seed_root / request.param / "agent_access.sql").read_text(encoding="utf-8")


def test_both_schemas_offer_a_view_of_every_table(tenant_sql, dataset) -> None:
    tenant, sql = tenant_sql
    tables = set(re.findall(rf"CREATE TABLE {tenant.schema}\.(\w+)", (dataset.seed_root / tenant.tenant / "schema.sql").read_text()))
    for schema in access.VARIANTS.values():
        views = set(re.findall(rf"CREATE VIEW {schema}\.(\w+)", sql))
        assert tables <= views, (schema, tables - views)
    assert set(re.findall(r"CREATE VIEW agent\.(\w+)", sql)) == set(re.findall(r"CREATE VIEW agent_raw\.(\w+)", sql))


def test_no_personal_column_reaches_the_scrubbed_schema_in_the_clear(tenant_sql) -> None:
    tenant, sql = tenant_sql
    for table, personal in tenant.personal.items():
        made = re.search(rf"CREATE MATERIALIZED VIEW agent_private\.{table} AS SELECT (.*?) FROM", sql).group(1)
        for p in personal:
            pseudonymized = f"agent_private.pseudonym('{p.kind}', ({p.expression})::text) AS {p.column}"
            assert pseudonymized in made, (table, p.column)
            made = made.replace(pseudonymized, "")
        for p in personal:
            for column in (*p.replaces, p.column):
                assert not re.search(rf"\bt\.{column}\b", made), (table, column)
        assert f"CREATE VIEW agent.{table} WITH (security_barrier) AS SELECT * FROM agent_private.{table} t" in sql


def test_every_role_reads_its_own_schema_and_level(tenant_sql) -> None:
    tenant, sql = tenant_sql
    for name, variant, level in access.roles(tenant.tenant):
        assert f"ALTER ROLE {name} IN DATABASE {tenant.database} SET search_path = {access.VARIANTS[variant]};" in sql
        assert f"GRANT SELECT ON ALL TABLES IN SCHEMA {access.VARIANTS[variant]} TO {name};" in sql
        assert f"INSERT INTO agent_private.role_levels VALUES ('{name}', '{level}');" in sql
    assert not [line for line in sql.splitlines() if "GRANT" in line and "agent_private" in line]


# -- against the loaded database -------------------------------------------------------------


try:
    import psycopg as _psycopg
except ImportError:  # a dev dependency only: the generator does not need it
    _psycopg = None


def _connect(role: str, database: str):
    return _psycopg.connect(host=HOST, port=PORT, user=role, password=access.password(role), dbname=database, connect_timeout=3)


def _reachable() -> bool:
    if _psycopg is None:
        return False
    try:
        _connect(access.role("empire", "raw", "PUBLIC"), "empire_inc").close()
        return True
    except _psycopg.Error:
        return False


live = pytest.mark.skipif(not _reachable(), reason=f"no loaded database at {HOST}:{PORT} (docker compose up)")


def _query(role: str, sql: str, database: str = "empire_inc") -> list[tuple]:
    with _connect(role, database) as connection:
        return connection.execute(sql).fetchall()


@live
def test_the_scrubbed_views_show_the_reference_pseudonyms(dataset) -> None:
    role = access.role("empire", "scrubbed", "RESTRICTED")
    employees = {row["employee_id"]: row for row in dataset.table("empire", "employees")}
    private = {row["employee_id"]: row for row in dataset.table("empire", "employee_private")}
    for employee_id, name, email in _query(role, "SELECT employee_id, name, email FROM employees ORDER BY employee_id LIMIT 25"):
        row = employees[employee_id]
        assert name == access.pseudonym("PERSON", f"{row['first_name']} {row['last_name']}", KEY)
        assert email == access.pseudonym("EMAIL", row["email"], KEY)
    for employee_id, salary, address in _query(role, "SELECT employee_id, salary_credits, home_address FROM employee_private LIMIT 25"):
        assert salary == access.pseudonym("SALARY", private[employee_id]["salary_credits"], KEY)
        assert address == access.pseudonym("ADDRESS", private[employee_id]["home_address"], KEY)


@live
def test_rows_above_a_roles_level_are_not_there(dataset) -> None:
    documents = dataset.table("empire", "documents")
    for level in LABELS:
        allowed = sum(1 for d in documents if LABELS.index(d["sensitivity"]) <= LABELS.index(level))
        assert _query(access.role("empire", "raw", level), "SELECT count(*) FROM documents") == [(allowed,)], level


@live
def test_the_summaries_match_their_rule(dataset) -> None:
    for view, (rule, table) in access.SUMMARIES.items():
        expected = rule(dataset.table("empire", "employees"), dataset.table("empire", table), dataset.table("empire", "departments"))
        got = _query(access.role("empire", "scrubbed", "CONFIDENTIAL"), f"SELECT * FROM {view}")
        assert sorted(tuple(str(v) for v in row) for row in got) == sorted(tuple(str(v) for v in row.values()) for row in expected), view
        assert _query(access.role("empire", "scrubbed", "INTERNAL"), f"SELECT count(*) FROM {view}") == [(0,)], view


@live
def test_an_agent_role_reaches_nothing_else() -> None:
    role = access.role("empire", "scrubbed", "RESTRICTED")
    for sql in (
        "SELECT 1 FROM empire.employees",
        "SELECT key FROM agent_private.pseudonym_key",
        "SELECT agent_private.pseudonym('PERSON', 'Mira Kestrel')",
        "SELECT 1 FROM agent_raw.employees",
        "SELECT set_config('role', 'empire', false)",
        "CREATE TABLE note (x int)",
    ):
        with pytest.raises(_psycopg.Error):
            _query(role, sql)
    with pytest.raises(_psycopg.Error):
        _query(access.role("kdy", "raw", "RESTRICTED"), "SELECT 1")
