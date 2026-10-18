"""Build the whole dataset: both buckets, both databases' seed data and the ground truth.

The output root receives four generated paths, which are deleted and rebuilt
on every run:

    bucket/<bucket name>/...    one folder per S3 bucket
    db/seed/<tenant>/...        schema.sql, load.sql and one CSV per table
    ground_truth/...            questions, manifest, logins, access matrix
    checksums.sha256            sha256 of every generated file
"""

import hashlib
import shutil
from pathlib import Path

from generator import agent_access, database, empire_db, facilities, ground_truth, questions
from generator.context import Context
from generator.docs import business, comms, messy, technical, testcases
from generator.kdy import context as kdy_context
from generator.kdy import db as kdy_db
from generator.kdy import docs as kdy_docs
from generator.kdy.context import KdyContext
from generator.pipeline import make_context
from generator.truth import Collector

GENERATED = ("bucket", "db/seed", "ground_truth", "checksums.sha256")


def _clean(out: Path) -> None:
    for relative in GENERATED:
        path = out / relative
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def _checksums(out: Path) -> str:
    files = sorted(p for relative in GENERATED[:-1] for p in (out / relative).rglob("*") if p.is_file())
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}" for p in files]
    return "\n".join(lines) + "\n"


def _personal(ctx: Context, kctx: KdyContext) -> tuple[frozenset[str], frozenset[str]]:
    """Every person's name, and every other personal value, of both tenants."""
    people = [*ctx.personnel.employees, *kctx.data.employees]
    names = {e.name for e in people} | {s["contact_name"] for s in ctx.supply.suppliers}
    values = {value for e in people for value in (e.email, e.home_address, e.personal_comlink)}
    values |= {e.badge_number for e in ctx.personnel.employees} | {s["contact_email"] for s in ctx.supply.suppliers}
    return frozenset(names), frozenset(values)


def build(out: Path) -> dict:
    _clean(out)
    collector = Collector()
    bucket_root = out / "bucket"

    ctx = make_context(bucket_root, collector)
    technical.build(ctx)
    testcases.build(ctx)
    business.build(ctx)
    comms.build(ctx)
    messy.build(ctx)
    questions.build(ctx)

    kctx = kdy_context.make_context(bucket_root, collector, ctx.supply, {(e.first_name, e.last_name) for e in ctx.personnel.employees})
    kdy_docs.build(kctx, questions.reverse_isolation_facts(ctx))

    seeds = (
        (agent_access.EMPIRE, empire_db.SCHEMA, empire_db.tables(ctx, facilities.build_access_logs(ctx.personnel, ctx.store))),
        (agent_access.KDY, kdy_db.SCHEMA, kdy_db.tables(kctx)),
    )
    for access, schema, tables in seeds:
        folder = out / "db" / "seed" / access.tenant
        database.write(folder, schema, tables)
        agent_access.write(folder, access, [table for table, _ in tables])

    summary = ground_truth.write(out / "ground_truth", collector, {"empire": ctx.store, "kdy": kctx.store},
                                 {"empire": ctx.personnel.logins, "kdy": kctx.data.logins}, _personal(ctx, kctx))
    (out / "checksums.sha256").write_text(_checksums(out), encoding="utf-8")
    return summary
