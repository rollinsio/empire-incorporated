"""Assemble the structured data and the build context in dependency order."""

from pathlib import Path

from generator import canon, engineering, facilities, hr, personnel, programs, supply, telemetry
from generator.config import EMPIRE_BUCKET, EMPIRE_DATABASE
from generator.context import Context
from generator.docs.model import DocumentStore
from generator.truth import Collector, Recorder


def make_context(bucket_root: Path, collector: Collector) -> Context:
    staff = personnel.build()
    plan = programs.build(staff)
    supplies = supply.build(staff, plan)
    store = DocumentStore(root=bucket_root / EMPIRE_BUCKET, bucket=EMPIRE_BUCKET, company=canon.COMPANY)
    return Context(
        personnel=staff,
        hr=hr.build(staff),
        programs=plan,
        supply=supplies,
        telemetry=telemetry.build(),
        facilities=facilities.build(staff),
        engineering=engineering.build(staff, plan, supplies),
        store=store,
        truth=Recorder(collector=collector, store=store, tenant="empire", database=EMPIRE_DATABASE),
    )
