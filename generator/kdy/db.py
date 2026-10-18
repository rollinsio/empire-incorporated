"""Kuat Drive Yards' database: table specs and the rows that fill them."""

from generator.database import DOCUMENTS, Table, col, document_rows
from generator.kdy import world
from generator.kdy.context import KdyContext
from generator.labels import CONFIDENTIAL, INTERNAL, RESTRICTED

SCHEMA = "kdy"

DEPARTMENTS = Table("departments", "Company departments.", INTERNAL, (
    col("department_id", "text"), col("code", "text", True), col("name", "text", True), col("headcount", "integer", True),
), ("department_id",))

EMPLOYEES = Table("employees", "Current and former employees. Salaries and home contact details are in employee_private.", INTERNAL, (
    col("employee_id", "text"), col("first_name", "text", True), col("last_name", "text", True), col("email", "text", True),
    col("department_id", "text", True, "departments"), col("title", "text", True), col("grade", "integer", True),
    col("manager_id", "text", references="employees"), col("hire_date", "date", True), col("status", "text", True),
    col("termination_date", "date"), col("access_level", "text", True),
), ("employee_id",))

EMPLOYEE_PRIVATE = Table("employee_private", "Personal data: salary and home contact details.", RESTRICTED, (
    col("employee_id", "text", references="employees"), col("salary_credits", "numeric", True), col("home_address", "text", True),
    col("personal_comlink", "text", True),
), ("employee_id",))

CUSTOMERS = Table("customers", "Customers and their account managers.", INTERNAL, (
    col("customer_id", "text"), col("name", "text", True), col("planet", "text", True), col("tier", "text", True),
    col("account_manager_id", "text", True, "employees"), col("procurement_email", "text", True),
), ("customer_id",))

PRODUCTS = Table("products", "Product catalogue with public list price and internal standard cost.", CONFIDENTIAL, (
    col("product_id", "text"), col("name", "text", True), col("category", "text", True), col("unit", "text", True),
    col("list_price_credits", "numeric", True), col("standard_cost_credits", "numeric", True),
), ("product_id",))

QUOTES = Table("quotes", "Customer quotes with price, cost and margin (totals in Mcr).", CONFIDENTIAL, (
    col("quote_id", "text"), col("customer_id", "text", True, "customers"), col("quote_date", "date", True), col("valid_until", "date", True),
    col("status", "text", True), col("total_price_mcr", "numeric", True), col("total_cost_mcr", "numeric", True), col("margin_pct", "numeric", True),
    col("prepared_by", "text", True, "employees"), col("approved_by", "text", True, "employees"),
), ("quote_id",))

QUOTE_LINES = Table("quote_lines", "Quote lines with unit price and unit cost.", CONFIDENTIAL, (
    col("quote_id", "text", references="quotes"), col("line_no", "integer"), col("product_id", "text", True, "products"),
    col("description", "text", True), col("quantity", "integer", True), col("unit_price_credits", "numeric", True),
    col("unit_cost_credits", "numeric", True),
), ("quote_id", "line_no"))

SALES_ORDERS = Table("sales_orders", "Sales orders with value, cost and margin. customer_po is the customer's own order number.", CONFIDENTIAL, (
    col("so_id", "text"), col("customer_id", "text", True, "customers"), col("customer_po", "text", True), col("order_date", "date", True),
    col("value_credits", "numeric", True), col("cost_credits", "numeric", True), col("margin_pct", "numeric", True), col("status", "text", True),
), ("so_id",))

PRODUCTION_LOTS = Table("production_lots", "Fabrication lots per sales order.", INTERNAL, (
    col("lot_id", "text"), col("so_id", "text", True, "sales_orders"), col("bay", "text", True), col("supervisor_id", "text", True, "employees"),
    col("start_date", "date", True), col("finish_date", "date"), col("planned_hours", "integer", True), col("actual_hours", "integer"),
    col("status", "text", True),
), ("lot_id",))

COST_RATES = Table("cost_rates", "Internal labour rates and overhead per department and year.", CONFIDENTIAL, (
    col("rate_id", "text"), col("fiscal_year", "integer", True), col("department_id", "text", True, "departments"),
    col("labour_rate_credits_per_hour", "numeric", True), col("overhead_pct", "numeric", True),
), ("rate_id",))

CONTRACT_MARGINS = Table("contract_margins", "Revenue, cost, margin and walk-away price per customer contract (Mcr).", CONFIDENTIAL, (
    col("contract_ref", "text"), col("customer_id", "text", True, "customers"), col("quote_id", "text", references="quotes"),
    col("start_date", "date", True), col("end_date", "date", True), col("revenue_mcr", "numeric", True), col("cost_mcr", "numeric", True),
    col("margin_pct", "numeric", True), col("walk_away_mcr", "numeric", True), col("renewal_target_margin_pct", "numeric", True),
), ("contract_ref",))


def tables(kctx: KdyContext) -> list[tuple[Table, list[dict]]]:
    people = kctx.data.employees
    return [
        (DEPARTMENTS, [{"department_id": dept_id, "code": code, "name": name, "headcount": headcount} for dept_id, code, name, headcount in world.DEPARTMENTS]),
        (EMPLOYEES, [{**vars(e), "department_id": world.DEPT_ID[e.department]} for e in people]),
        (EMPLOYEE_PRIVATE, [{"employee_id": e.employee_id, "salary_credits": e.salary, "home_address": e.home_address,
                             "personal_comlink": e.personal_comlink} for e in people]),
        (CUSTOMERS, kctx.data.customers),
        (PRODUCTS, kctx.data.products),
        (QUOTES, kctx.data.quotes),
        (QUOTE_LINES, kctx.data.quote_lines),
        (SALES_ORDERS, kctx.data.sales_orders),
        (PRODUCTION_LOTS, kctx.data.production_lots),
        (COST_RATES, kctx.data.cost_rates),
        (CONTRACT_MARGINS, kctx.data.contract_margins),
        (DOCUMENTS, document_rows(kctx.store)),
    ]
