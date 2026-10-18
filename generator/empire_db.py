"""Empire Incorporated's database: table specs and the rows that fill them."""

from generator import canon
from generator.context import Context
from generator.database import DOCUMENTS, Table, col, document_rows
from generator.labels import CONFIDENTIAL, INTERNAL, RESTRICTED
from generator.personnel import history_id

SCHEMA = "empire"

DEPARTMENTS = Table("departments", "Company departments.", INTERNAL, (
    col("department_id", "text"), col("code", "text", True), col("name", "text", True), col("headcount", "integer", True),
), ("department_id",))

LOCATIONS = Table("locations", "Depots, facilities and the station receiving bay that hold inventory.", INTERNAL, (
    col("location_code", "text"), col("name", "text", True), col("location_type", "text", True), col("planet", "text", True),
), ("location_code",))

EMPLOYEES = Table("employees", "Current and former employees. Salaries and home contact details are in employee_private.", INTERNAL, (
    col("employee_id", "text"), col("badge_number", "text", True), col("first_name", "text", True), col("last_name", "text", True),
    col("email", "text", True), col("species", "text", True), col("homeworld", "text", True),
    col("department_id", "text", True, "departments"), col("title", "text", True), col("grade", "integer", True),
    col("manager_id", "text", references="employees"), col("hire_date", "date", True), col("status", "text", True),
    col("termination_date", "date"), col("termination_reason", "text"), col("work_location", "text", True),
    col("language", "text", True), col("comm_extension", "text", True), col("access_level", "text", True),
), ("employee_id",))

EMPLOYEE_PRIVATE = Table("employee_private", "Personal data: current salary and home contact details.", RESTRICTED, (
    col("employee_id", "text", references="employees"), col("salary_credits", "numeric", True), col("home_address", "text", True),
    col("personal_comlink", "text", True), col("emergency_contact", "text", True),
), ("employee_id",))

EMPLOYMENT_HISTORY = Table("employment_history", "Every hire, promotion, transfer and departure: department, title, grade and manager from that date.", INTERNAL, (
    col("history_id", "text"), col("employee_id", "text", True, "employees"), col("effective_date", "date", True), col("event", "text", True),
    col("department_id", "text", True, "departments"), col("title", "text", True), col("grade", "integer", True),
    col("manager_id", "text", references="employees"), col("note", "text"),
), ("history_id",))

COMPENSATION_HISTORY = Table("compensation_history", "The salary that applied from each employment event.", RESTRICTED, (
    col("history_id", "text", references="employment_history"), col("employee_id", "text", True, "employees"),
    col("effective_date", "date", True), col("salary_credits", "numeric", True), col("event", "text", True),
), ("history_id",))

LEADERSHIP = Table("leadership", "Who led each department and program, and when. end_date empty = current.", INTERNAL, (
    col("leadership_id", "text"), col("entity_type", "text", True), col("entity_id", "text", True), col("role", "text", True),
    col("employee_id", "text", True, "employees"), col("start_date", "date", True), col("end_date", "date"),
), ("leadership_id",))

PERFORMANCE_REVIEWS = Table("performance_reviews", "Annual performance reviews.", RESTRICTED, (
    col("review_id", "text"), col("employee_id", "text", True, "employees"), col("cycle_year", "integer", True),
    col("reviewer_id", "text", True, "employees"), col("review_date", "date", True), col("rating", "integer", True),
    col("rating_label", "text", True), col("strengths", "text", True), col("development", "text", True),
    col("salary_increase_pct", "numeric", True),
), ("review_id",))

PROGRAMS = Table("programs", "Company programs with their total budget in millions of credits (Mcr).", CONFIDENTIAL, (
    col("program_id", "text"), col("code", "text", True), col("name", "text", True),
    col("executive_sponsor_id", "text", True, "employees"), col("program_director_id", "text", True, "employees"),
    col("status", "text", True), col("start_date", "date", True), col("target_completion", "date", True), col("budget_mcr", "numeric", True),
), ("program_id",))

SYSTEMS = Table("systems", "Station subsystems.", INTERNAL, (
    col("system_code", "text"), col("name", "text", True), col("lead_department_id", "text", True, "departments"), col("summary", "text", True),
), ("system_code",))

SUPPLIERS = Table("suppliers", "Suppliers and their main contact.", INTERNAL, (
    col("supplier_id", "text"), col("name", "text", True), col("homeworld", "text", True), col("contact_name", "text", True),
    col("contact_email", "text", True), col("status", "text", True), col("performance_rating", "numeric", True),
), ("supplier_id",))

WORK_PACKAGES = Table("work_packages", "Work packages with budget and actual cost in Mcr.", CONFIDENTIAL, (
    col("wp_id", "text"), col("program_id", "text", True, "programs"), col("wbs_code", "text", True), col("name", "text", True),
    col("system_code", "text", references="systems"), col("component_code", "text", references="components"),
    col("owner_id", "text", True, "employees"), col("department_id", "text", True, "departments"),
    col("start_date", "date", True), col("end_date", "date", True), col("budget_mcr", "numeric", True), col("actual_mcr", "numeric", True),
    col("percent_complete", "numeric", True), col("status", "text", True),
), ("wp_id",))

COMPONENTS = Table("components", "Station components and their controlling documents.", INTERNAL, (
    col("component_code", "text"), col("system_code", "text", True, "systems"), col("name", "text", True),
    col("spec_number", "text", True), col("spec_revision", "text", True), col("drawing_number", "text", True), col("bom_number", "text", True),
    col("engineer_id", "text", True, "employees"), col("approver_id", "text", True, "employees"),
    col("supplier_id", "text", True, "suppliers"), col("work_package_id", "text", references="work_packages"),
), ("component_code",))

COMPONENT_PARAMETERS = Table("component_parameters", "Approved required value of every component parameter.", INTERNAL, (
    col("req_id", "text"), col("component_code", "text", True, "components"), col("name", "text", True), col("unit", "text"),
    col("value", "numeric", True), col("tolerance_pct", "numeric", True), col("verification", "text", True),
), ("req_id",))

MILESTONES = Table("milestones", "Program and work-package milestones.", INTERNAL, (
    col("milestone_id", "text"), col("program_id", "text", True, "programs"), col("wp_id", "text", references="work_packages"),
    col("name", "text", True), col("planned_date", "date", True), col("forecast_date", "date", True), col("actual_date", "date"),
    col("status", "text", True),
), ("milestone_id",))

TASKS = Table("tasks", "Work-package tasks.", INTERNAL, (
    col("task_id", "text"), col("wp_id", "text", True, "work_packages"), col("title", "text", True),
    col("assignee_id", "text", True, "employees"), col("status", "text", True), col("priority", "text", True),
    col("created_date", "date", True), col("due_date", "date", True), col("completed_date", "date"), col("estimate_hours", "integer", True),
), ("task_id",))

BUDGET_LINES = Table("budget_lines", "Quarterly planned and actual spend per program and category, in Mcr.", CONFIDENTIAL, (
    col("budget_line_id", "text"), col("program_id", "text", True, "programs"), col("fiscal_year", "integer", True),
    col("quarter", "integer", True), col("category", "text", True), col("planned_mcr", "numeric", True), col("actual_mcr", "numeric"),
), ("budget_line_id",))

MATERIALS = Table("materials", "Material catalogue with standard unit cost in credits.", INTERNAL, (
    col("material_id", "text"), col("sku", "text", True), col("name", "text", True), col("category", "text", True),
    col("system_code", "text", True, "systems"), col("unit", "text", True), col("unit_cost_credits", "numeric", True),
    col("strategic", "boolean", True), col("hazardous", "boolean", True),
), ("material_id",))

CONTRACTS = Table("contracts", "Supplier contracts with their total value in Mcr.", CONFIDENTIAL, (
    col("contract_id", "text"), col("supplier_id", "text", True, "suppliers"), col("title", "text", True),
    col("start_date", "date", True), col("end_date", "date", True), col("value_mcr", "numeric", True),
    col("owner_id", "text", True, "employees"), col("status", "text", True),
), ("contract_id",))

PURCHASE_ORDERS = Table("purchase_orders", "Purchase orders with their total in credits.", CONFIDENTIAL, (
    col("po_id", "text"), col("po_number", "text", True), col("supplier_id", "text", True, "suppliers"),
    col("wp_id", "text", True, "work_packages"), col("requested_by", "text", True, "employees"), col("approved_by", "text", True, "employees"),
    col("order_date", "date", True), col("status", "text", True), col("total_credits", "numeric", True),
), ("po_id",))

PO_LINES = Table("po_lines", "Purchase order lines.", CONFIDENTIAL, (
    col("po_id", "text", references="purchase_orders"), col("line_no", "integer"), col("material_id", "text", True, "materials"),
    col("quantity", "integer", True), col("unit_price_credits", "numeric", True), col("line_total_credits", "numeric", True),
    col("delivery_date", "date", True),
), ("po_id", "line_no"))

INVENTORY = Table("inventory", "Stock on hand per material and location.", INTERNAL, (
    col("inventory_id", "text"), col("material_id", "text", True, "materials"), col("location_code", "text", True, "locations"),
    col("quantity_on_hand", "integer", True), col("quantity_reserved", "integer", True), col("last_counted", "date", True),
), ("inventory_id",))

ZONES = Table("zones", "The 24 construction zones of the station sphere.", INTERNAL, (
    col("zone_code", "text"), col("name", "text", True),
), ("zone_code",))

ZONE_PROGRESS = Table("zone_progress", "Daily construction progress per zone.", INTERNAL, (
    col("zone_code", "text", references="zones"), col("progress_date", "date"), col("percent_complete", "numeric", True),
    col("crew_on_shift", "integer", True), col("hours_worked", "integer", True), col("safety_incidents", "integer", True),
), ("zone_code", "progress_date"))

SENSORS = Table("sensors", "Station sensors.", INTERNAL, (
    col("sensor_id", "text"), col("system_code", "text", True, "systems"), col("zone_code", "text", True, "zones"),
    col("metric", "text", True), col("unit", "text", True),
), ("sensor_id",))

SENSOR_READINGS = Table("sensor_readings", "Hourly sensor readings, August and September 2026 (UTC).", INTERNAL, (
    col("sensor_id", "text", references="sensors"), col("reading_at", "timestamptz"), col("value", "double precision", True),
), ("sensor_id", "reading_at"))

FACILITY_INCIDENTS = Table("facility_incidents", "Facility and workplace-safety incidents.", INTERNAL, (
    col("incident_id", "text"), col("opened_date", "date", True), col("closed_date", "date"), col("severity", "text", True),
    col("category", "text", True), col("summary", "text", True), col("status", "text", True),
    col("reported_by", "text", True, "employees"),
), ("incident_id",))

DOCUMENT_ACCESS_LOG = Table("document_access_log", "Document opens, January to September 2026 (UTC).", INTERNAL, (
    col("log_id", "integer"), col("accessed_at", "timestamptz", True), col("employee_id", "text", True, "employees"),
    col("document_id", "text", True, "documents"), col("action", "text", True), col("terminal_id", "text", True), col("result", "text", True),
), ("log_id",))


def _employee_rows(ctx: Context) -> tuple[list[dict], list[dict], list[dict]]:
    employees, private, history = [], [], []
    for e in ctx.personnel.employees:
        employees.append({
            "employee_id": e.employee_id, "badge_number": e.badge_number, "first_name": e.first_name, "last_name": e.last_name,
            "email": e.email, "species": e.species, "homeworld": e.homeworld, "department_id": canon.DEPT_ID[e.department],
            "title": e.title, "grade": e.grade, "manager_id": e.manager_id, "hire_date": e.hire_date, "status": e.status,
            "termination_date": e.termination_date, "termination_reason": e.termination_reason, "work_location": e.work_location,
            "language": e.language, "comm_extension": e.comm_extension, "access_level": e.access_level,
        })
        private.append({"employee_id": e.employee_id, "salary_credits": e.salary, "home_address": e.home_address,
                        "personal_comlink": e.personal_comlink, "emergency_contact": e.emergency_contact})
        for n, stint in enumerate(e.history, start=1):
            history.append({
                "history_id": history_id(e.employee_id, n), "employee_id": e.employee_id, "effective_date": stint.start,
                "event": stint.event, "department_id": canon.DEPT_ID[stint.department], "title": stint.title, "grade": stint.grade,
                "manager_id": stint.manager_id, "salary_credits": stint.salary, "note": stint.note,
            })
    return employees, private, history


def _component_rows(ctx: Context) -> tuple[list[dict], list[dict]]:
    components, parameters = [], []
    for c in ctx.engineering.components:
        components.append({
            "component_code": c.code, "system_code": c.system_code, "name": c.name, "spec_number": c.spec_number,
            "spec_revision": c.spec_revision, "drawing_number": c.drawing_number, "bom_number": c.bom_number,
            "engineer_id": c.engineer_id, "approver_id": c.approver_id, "supplier_id": c.supplier_id,
            "work_package_id": c.work_package_id, "sensitivity": c.label,
        })
        parameters += [{"req_id": p.req_id, "component_code": c.code, "name": p.name, "unit": p.unit or None, "value": p.value,
                        "tolerance_pct": p.tolerance_pct, "verification": p.verification, "sensitivity": c.label} for p in c.params]
    return components, parameters


def _work_package_rows(ctx: Context) -> list[dict]:
    return [{**vars(wp), "department_id": canon.DEPT_ID[wp.department]} for wp in ctx.programs.work_packages]


def tables(ctx: Context, access_log: list[dict]) -> list[tuple[Table, list[dict]]]:
    employees, private, history = _employee_rows(ctx)
    components, parameters = _component_rows(ctx)
    sensor_labels = {s["sensor_id"]: s["sensitivity"] for s in ctx.telemetry.sensors}
    return [
        (DEPARTMENTS, [{"department_id": dept_id, "code": code, "name": name, "headcount": headcount} for dept_id, code, name, headcount in canon.DEPARTMENTS]),
        (LOCATIONS, ctx.supply.locations),
        (EMPLOYEES, employees),
        (EMPLOYEE_PRIVATE, private),
        (EMPLOYMENT_HISTORY, history),
        (COMPENSATION_HISTORY, history),
        (LEADERSHIP, ctx.personnel.leadership),
        (PERFORMANCE_REVIEWS, ctx.hr.reviews),
        (PROGRAMS, ctx.programs.programs),
        (SYSTEMS, ctx.programs.systems),
        (SUPPLIERS, ctx.supply.suppliers),
        (WORK_PACKAGES, _work_package_rows(ctx)),
        (COMPONENTS, components),
        (COMPONENT_PARAMETERS, parameters),
        (MILESTONES, ctx.programs.milestones),
        (TASKS, ctx.programs.tasks),
        (BUDGET_LINES, ctx.programs.budget_lines),
        (MATERIALS, ctx.supply.materials),
        (CONTRACTS, ctx.supply.contracts),
        (PURCHASE_ORDERS, ctx.supply.purchase_orders),
        (PO_LINES, ctx.supply.po_lines),
        (INVENTORY, ctx.supply.inventory),
        (ZONES, [{"zone_code": code, "name": name} for code, name in canon.ZONES]),
        (ZONE_PROGRESS, ctx.telemetry.progress),
        (SENSORS, ctx.telemetry.sensors),
        (SENSOR_READINGS, [{**row, "sensitivity": sensor_labels[row["sensor_id"]]} for row in ctx.telemetry.readings]),
        (FACILITY_INCIDENTS, ctx.facilities.incidents),
        (DOCUMENTS, document_rows(ctx.store)),
        (DOCUMENT_ACCESS_LOG, access_log),
    ]
