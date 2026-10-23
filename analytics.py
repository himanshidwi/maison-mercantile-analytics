"""Reusable analytics functions for the AI Business Analyst Assistant.

This module reads from the existing DuckDB database and does not modify data.
"""

from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd
import calendar


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "business_analytics.duckdb"


def run_query(sql: str, params: Optional[list] = None) -> pd.DataFrame:
    """Run a read-only SQL query against the existing DuckDB database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB database not found at {DB_PATH}. "
            "Keep analytics.py in the same folder as business_analytics.duckdb."
        )

    # Use a read-only connection so analytics functions cannot change the database.
    with duckdb.connect(str(DB_PATH), read_only=True) as connection:
        return connection.execute(sql, params or []).df()


def get_monthly_revenue(start_month: str, end_month: str,
                        country: Optional[str] = None) -> pd.DataFrame:
    """Return monthly net line revenue for YYYY-MM month boundaries.

    Revenue is Quantity * UnitPrice, including negative quantities.
    """
    _validate_month(start_month)
    _validate_month(end_month)
    if start_month > end_month:
        raise ValueError("end_month must be on or after start_month")

    where = """
        InvoiceDate >= CAST(? AS DATE)
        AND InvoiceDate < CAST(? AS DATE) + INTERVAL 1 MONTH
    """
    params = [f"{start_month}-01", f"{end_month}-01"]

    if country and country != "All countries":
        where += " AND Country = ?"
        params.append(country)

    sql = f"""
        SELECT
            STRFTIME(InvoiceDate, '%Y-%m') AS month,
            SUM(Revenue) AS net_revenue,
            SUM(CASE WHEN Quantity > 0 THEN Revenue ELSE 0 END) AS positive_sales,
            -SUM(CASE WHEN Quantity < 0 THEN Revenue ELSE 0 END) AS negative_line_value
        FROM retail_sales
        WHERE {where}
        GROUP BY STRFTIME(InvoiceDate, '%Y-%m')
        ORDER BY month
    """
    return run_query(sql, params)


def get_top_countries(start_month: str, end_month: str,
                      limit: int = 10) -> pd.DataFrame:
    """Return countries ranked by net line revenue for a month range."""
    _validate_month(start_month)
    _validate_month(end_month)
    if start_month > end_month:
        raise ValueError("end_month must be on or after start_month")
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        raise ValueError("limit must be an integer from 1 to 100")

    sql = """
        SELECT
            Country,
            SUM(Revenue) AS net_revenue,
            COUNT(DISTINCT CASE
                WHEN NOT STARTS_WITH(CAST(InvoiceNo AS VARCHAR), 'C')
                THEN InvoiceNo END
            ) AS non_cancel_invoice_ids,
            COUNT(DISTINCT CustomerID) AS identified_customers
        FROM retail_sales
        WHERE InvoiceDate >= CAST(? AS DATE)
          AND InvoiceDate < CAST(? AS DATE) + INTERVAL 1 MONTH
          AND Country IS NOT NULL
        GROUP BY Country
        ORDER BY net_revenue DESC
        LIMIT ?
    """
    return run_query(sql, [f"{start_month}-01", f"{end_month}-01", limit])


def _validate_month(value: str) -> None:
    """Validate YYYY-MM month strings."""
    if not isinstance(value, str) or len(value) != 7 or value[4] != "-":
        raise ValueError("Month must use YYYY-MM format, for example '2011-03'.")

    try:
        year = int(value[:4])
        month = int(value[5:7])
    except ValueError as exc:
        raise ValueError("Month must use YYYY-MM format, for example '2011-03'.") from exc

    if year < 1900 or not 1 <= month <= 12:
        raise ValueError("Invalid month. Use YYYY-MM format, for example '2011-03'.")




def answer_business_question(question: str) -> str:
    """Answer supported business questions using DuckDB data."""
    import re
    import calendar

    if not isinstance(question, str) or not question.strip():
        return "Please enter a business question."

    q = question.lower().strip()

    month_map = {
        name.lower(): f"{i:02d}"
        for i, name in enumerate(calendar.month_name)
        if name
    }

    found_months = []
    for name, number in month_map.items():
        if re.search(rf"\b{name}\b", q):
            found_months.append((name, number))

    year_match = re.search(r"\b(2010|2011)\b", q)
    year = year_match.group(1) if year_match else "2011"

    # Negative net revenue by country.
    if "negative" in q and any(
        word in q for word in ["country", "countries", "revenue", "market"]
    ):
        month_number = found_months[0][1] if found_months else None
        if not month_number:
            return "Please specify a month, for example January 2011."

        month = f"{year}-{month_number}"
        data = run_query(
            """
            SELECT Country, ROUND(SUM(Revenue), 2) AS net_revenue
            FROM retail_sales
            WHERE STRFTIME(InvoiceDate, '%Y-%m') = ?
              AND Country IS NOT NULL
            GROUP BY Country
            HAVING SUM(Revenue) < 0
            ORDER BY net_revenue ASC
            """,
            [month],
        )

        if data.empty:
            return f"No countries had negative net revenue in {calendar.month_name[int(month_number)]} {year}."

        lines = [
            f"{row.Country}: £{row.net_revenue:,.2f}"
            for row in data.itertuples(index=False)
        ]
        return (
            f"Countries with negative net revenue in "
            f"{calendar.month_name[int(month_number)]} {year}:\n\n"
            + "\n".join(lines)
        )

    # Compare two requested months.
    if any(word in q for word in ["compare", "comparison", "versus", " vs "]):
        if len(found_months) < 2:
            return "Please specify two months, for example: Compare January and February 2011 revenue."

        month_values = [f"{year}-{number}" for _, number in found_months[:2]]
        data = run_query(
            """
            SELECT STRFTIME(InvoiceDate, '%Y-%m') AS month,
                   ROUND(SUM(Revenue), 2) AS net_revenue
            FROM retail_sales
            WHERE STRFTIME(InvoiceDate, '%Y-%m') IN (?, ?)
            GROUP BY STRFTIME(InvoiceDate, '%Y-%m')
            ORDER BY month
            """,
            month_values,
        )

        revenue_by_month = dict(zip(data["month"], data["net_revenue"]))
        answers = []
        for month in month_values:
            label = calendar.month_name[int(month[-2:])] + " " + month[:4]
            if month in revenue_by_month:
                answers.append(f"{label}: £{revenue_by_month[month]:,.2f}")
            else:
                answers.append(f"{label}: no data")

        if len(data) == 2:
            first, second = month_values
            difference = revenue_by_month[second] - revenue_by_month[first]
            answers.append(f"Change from {first} to {second}: £{difference:,.2f}")

        return "\n".join(answers)

    # Highest or lowest country revenue.
    if any(word in q for word in ["country", "countries", "market"]):
        month_number = found_months[0][1] if found_months else None
        if month_number:
            start_month = end_month = f"{year}-{month_number}"
        else:
            start_month, end_month = "2010-12", "2011-12"

        data = run_query(
            """
            SELECT Country, ROUND(SUM(Revenue), 2) AS net_revenue
            FROM retail_sales
            WHERE STRFTIME(InvoiceDate, '%Y-%m') BETWEEN ? AND ?
              AND Country IS NOT NULL
            GROUP BY Country
            ORDER BY net_revenue
            """,
            [start_month, end_month],
        )

        if data.empty:
            return "No country revenue data was found."

        lowest = any(word in q for word in ["lowest", "least", "minimum", "smallest"])
        result = data.iloc[0] if lowest else data.iloc[-1]
        direction = "lowest" if lowest else "highest"
        period = (
            f"in {calendar.month_name[int(month_number)]} {year}"
            if month_number else "across the dataset period"
        )
        return (
            f"{result['Country']} generated the {direction} net revenue "
            f"{period}, at £{result['net_revenue']:,.2f}."
        )

    # Individual month revenue.
    if found_months and any(word in q for word in ["revenue", "sales", "month"]):
        month = f"{year}-{found_months[0][1]}"
        data = get_monthly_revenue(month, month)
        if data.empty:
            return f"No revenue data was found for {month}."

        value = data.iloc[0]["net_revenue"]
        answer = f"Net revenue for {month} was £{value:,.2f}."
        if month == "2011-12":
            answer += " This is partial-month revenue; the dataset ends on December 9, 2011."
        return answer

    return (
        "I can answer questions about highest or lowest country revenue, "
        "countries with negative revenue, monthly revenue, and month comparisons."
    )
