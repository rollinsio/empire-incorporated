"""The engineering registry: one record per station component.

Specs, drawings, BOMs, test reports, the master specification and the ground
truth all read a component's required values from here, so every document
agrees on them. Components whose specification has conflicting revisions take
the *approved* value from ``canon``.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from generator import canon
from generator.personnel import Personnel
from generator.programs import Programs
from generator.rand import stream
from generator.supply import KDY, Supply

VERIFICATION_METHODS = ("Test", "Analysis", "Inspection", "Demonstration")

# Components whose specification is written by the conflicting-revision builder instead.
PLANTED_SPEC_NUMBERS = {(system, component): number for number, (system, component, *_rest) in canon.CONFLICTING_SPECS.items()}


@dataclass
class Parameter:
    req_id: str
    name: str
    unit: str
    value: float
    decimals: int
    tolerance_pct: float
    verification: str

    def formatted(self) -> str:
        value = f"{self.value:,.{self.decimals}f}"
        return f"{value} {self.unit}".strip()


@dataclass
class Component:
    code: str              # e.g. "HR-RCV"
    system_code: str
    short: str             # e.g. "RCV"
    name: str
    params: list[Parameter]
    spec_number: str
    spec_revision: str
    spec_date: date
    drawing_number: str
    bom_number: str
    engineer_id: str
    approver_id: str
    supplier_id: str
    work_package_id: str | None
    planted_spec: bool

    @property
    def system_name(self) -> str:
        return canon.SYSTEMS[self.system_code]["name"]

    @property
    def label(self) -> str:
        return canon.SYSTEMS[self.system_code]["label"]


@dataclass
class Engineering:
    components: list[Component]
    by_code: dict[str, Component]

    def for_system(self, system_code: str) -> list[Component]:
        return [c for c in self.components if c.system_code == system_code]


def _approved_override(system: str, short: str, param_name: str) -> float | None:
    for sys_code, comp, name, _unit, revisions in canon.CONFLICTING_SPECS.values():
        if (sys_code, comp, name) == (system, short, param_name):
            return next(value for value, status in revisions.values() if status == "APPROVED")
    return None


def _approved_revision(system: str, short: str) -> str | None:
    number = PLANTED_SPEC_NUMBERS.get((system, short))
    if number is None:
        return None
    return next(rev for rev, (_value, status) in canon.CONFLICTING_SPECS[number][4].items() if status == "APPROVED")


def build(personnel: Personnel, programs: Programs, supply: Supply) -> Engineering:
    rng = stream("engineering")
    components = []
    suppliers = [s["supplier_id"] for s in supply.suppliers]
    for code, spec in canon.SYSTEMS.items():
        dept = spec["dept"]
        engineers = [e for e in personnel.active(dept) if 6 <= e.grade <= 9]
        for index, (short, name, raw_params) in enumerate(spec["components"], start=1):
            params = []
            for n, (param_name, unit, low, high, decimals) in enumerate(raw_params, start=1):
                override = _approved_override(code, short, param_name)
                value = override if override is not None else round(rng.uniform(low, high), decimals)
                params.append(Parameter(
                    req_id=f"{code}-{short}-R{n:02d}", name=param_name, unit=unit, value=value, decimals=decimals,
                    tolerance_pct=rng.choice((0.5, 1.0, 2.0, 2.5, 5.0)) if low != high else 0.0,
                    verification=rng.choice(VERIFICATION_METHODS),
                ))
            planted = (code, short) in PLANTED_SPEC_NUMBERS
            spec_date = date(2022, 3, 1) + timedelta(days=rng.randint(0, 1200))
            head = personnel.head_of(dept, spec_date) or personnel.by_handle["kalvane"]
            wp = next((w for w in programs.work_packages if w.component_code == f"{code}-{short}"), None)
            components.append(Component(
                code=f"{code}-{short}", system_code=code, short=short, name=name, params=params,
                spec_number=PLANTED_SPEC_NUMBERS.get((code, short), f"SHV-{code}-SPEC-{100 + index:04d}"),
                spec_revision=_approved_revision(code, short) or rng.choice("ABBCCD"), spec_date=spec_date,
                drawing_number=f"SHV-{code}-DWG-{200 + index:04d}",
                bom_number=f"SHV-{code}-BOM-{300 + index:04d}",
                engineer_id=rng.choice(engineers).employee_id,
                approver_id=head.employee_id,
                supplier_id=KDY["supplier_id"] if code in KDY["systems"] and rng.random() < 0.5 else rng.choice(suppliers),
                work_package_id=wp.wp_id if wp else None,
                planted_spec=planted,
            ))
    return Engineering(components, {c.code: c for c in components})
