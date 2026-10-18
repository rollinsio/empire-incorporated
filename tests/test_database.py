"""The seed data matches its schema: headers, primary keys, required columns and foreign keys."""

import re

import pytest

from generator import empire_db
from generator.database import Table
from generator.kdy import db as kdy_db

SCHEMAS = {
    "empire": (empire_db.SCHEMA, [value for value in vars(empire_db).values() if isinstance(value, Table)]),
    "kdy": (kdy_db.SCHEMA, [value for value in vars(kdy_db).values() if isinstance(value, Table)]),
}
CASES = [(tenant, table) for tenant, (_, tables) in SCHEMAS.items() for table in tables]


def _ids(case) -> str:
    tenant, table = case
    return f"{tenant}.{table.name}"


@pytest.mark.parametrize("case", CASES, ids=[_ids(c) for c in CASES])
def test_table_matches_its_spec(dataset, case):
    tenant, table = case
    rows = dataset.table(tenant, table.name)
    assert rows, f"{table.name} is empty"
    assert list(rows[0]) == table.column_names
    keys = [tuple(row[c] for c in table.primary_key) for row in rows]
    assert len(keys) == len(set(keys)), "duplicate primary key"
    for column in table.columns:
        if column.required or column.name in table.primary_key:
            assert all(row[column.name] != "" for row in rows), f"empty required column {column.name}"


@pytest.mark.parametrize("case", CASES, ids=[_ids(c) for c in CASES])
def test_foreign_keys_resolve(dataset, case):
    tenant, table = case
    specs = {t.name: t for t in SCHEMAS[tenant][1]}
    rows = dataset.table(tenant, table.name)
    for column in table.columns:
        if not column.references:
            continue
        target_name, _, target_column = column.references.partition("(")
        target = specs[target_name]
        target_column = target_column.rstrip(")") or target.primary_key[0]
        valid = {row[target_column] for row in dataset.table(tenant, target_name)}
        missing = {row[column.name] for row in rows if row[column.name] and row[column.name] not in valid}
        assert not missing, f"{column.name} -> {target_name}: {sorted(missing)[:5]}"


@pytest.mark.parametrize("tenant", SCHEMAS)
def test_schema_and_load_scripts_cover_every_table(dataset, tenant):
    schema, tables = SCHEMAS[tenant]
    folder = dataset.seed_root / tenant
    created = set(re.findall(rf"CREATE TABLE {schema}\.(\w+)", (folder / "schema.sql").read_text(encoding="utf-8")))
    copied = set(re.findall(rf"\\copy {schema}\.(\w+)", (folder / "load.sql").read_text(encoding="utf-8")))
    names = {t.name for t in tables}
    assert created == copied == names == {p.stem for p in folder.glob("*.csv")}
