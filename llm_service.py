"""Local LLM service with data-backed retail product/market recommendations.

DuckDB computes all figures. The local LLM is used for question interpretation
and conceptual explanations; it does not invent or calculate financial metrics.
"""

import json
import re

import requests
import analytics

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"


def _call_llm(messages: list) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def _month_year(question: str):
    """Return (YYYY-MM, display label) if a month/year is present."""
    match = re.search(
        r"\b(january|february|march|april|may|june|july|august|"
        r"september|october|november|december)\s+(2010|2011)\b",
        question,
        re.IGNORECASE,
    )
    if not match:
        return None, None
    months = {
        "january": "01", "february": "02", "march": "03",
        "april": "04", "may": "05", "june": "06",
        "july": "07", "august": "08", "september": "09",
        "october": "10", "november": "11", "december": "12",
    }
    month_name = match.group(1).title()
    return f"{match.group(2)}-{months[match.group(1).lower()]}", f"{month_name} {match.group(2)}"


def _recommend_products_and_markets(question: str) -> str:
    """Rank product-market combinations using historical revenue and demand."""
    month, period_label = _month_year(question)
    if month:
        where = "STRFTIME(InvoiceDate, '%Y-%m') = ?"
        params = [month]
        scope = period_label
    else:
        where = "InvoiceDate >= DATE '2010-12-01' AND InvoiceDate < DATE '2011-12-10'"
        params = []
        scope = "the available dataset period (December 2010–December 2011)"

    sql = f"""
        SELECT
            Description AS product,
            Country AS country,
            ROUND(SUM(Revenue), 2) AS net_revenue,
            ROUND(SUM(CASE WHEN Quantity > 0 THEN Revenue ELSE 0 END), 2) AS positive_sales,
            SUM(CASE WHEN Quantity > 0 THEN Quantity ELSE 0 END) AS units_sold,
            COUNT(DISTINCT InvoiceNo) AS invoice_count,
            COUNT(DISTINCT CustomerID) AS identified_customers
        FROM retail_sales
        WHERE {where}
          AND Description IS NOT NULL
          AND Country IS NOT NULL
          AND Quantity > 0
        GROUP BY Description, Country
        HAVING SUM(CASE WHEN Quantity > 0 THEN Revenue ELSE 0 END) > 0
        ORDER BY positive_sales DESC
        LIMIT 12
    """
    data = analytics.run_query(sql, params)
    if data.empty:
        return f"I couldn't find product-and-country sales data for {scope}."

    lines = []
    for i, row in enumerate(data.head(8).itertuples(index=False), start=1):
        lines.append(
            f"{i}. {row.product} — {row.country}: positive sales "
            f"£{row.positive_sales:,.2f}; {int(row.units_sold):,} units; "
            f"{int(row.invoice_count):,} invoice IDs; "
            f"{int(row.identified_customers):,} identified customers."
        )

    return (
        f"## Product and market opportunities ({scope})\n\n"
        "These are the strongest product–country combinations by historical "
        "positive-quantity sales in the dataset:\n\n"
        + "\n".join(lines)
        + "\n\n**How to use this:** shortlist the combinations with strong sales, "
        "unit demand and invoice activity for further investigation. This dataset "
        "does not include product costs, margins, inventory, marketing spend or "
        "future demand, so it cannot prove which product will be most profitable "
        "or where additional investment will earn the best return. Check margins, "
        "stock availability, recent trend and fulfilment costs before committing."
    )


def ask_llm(question: str) -> str:
    """Interpret a question, query approved analytics, and explain the result."""
    if not isinstance(question, str) or not question.strip():
        return "Please enter a business question."

    q = question.strip()
    q_lower = q.lower()

    # Handle investment/where-to-sell questions deterministically so the model
    # cannot incorrectly classify them as unsupported.
    product_words = ("product", "products", "item", "items", "stock", "sell")
    investment_words = (
        "invest", "investment", "focus", "priorit", "prioritise", "prioritize",
        "push", "promote", "expand", "where", "market", "recommend",
    )
    if any(w in q_lower for w in product_words) and any(w in q_lower for w in investment_words):
        try:
            return _recommend_products_and_markets(q)
        except Exception as exc:
            return f"I couldn't analyse product and market performance: {exc}"

    # Existing supported data questions are classified by the local model.
    instructions = """
You classify questions about a retail sales dataset.
Return ONLY a JSON object with keys:
intent, month, year, comparison_month, comparison_year, direction.

Allowed intents:
country_ranking, negative_countries, monthly_revenue,
month_comparison, general_explanation, unsupported.

Rules:
- country_ranking: highest or lowest revenue by country.
- negative_countries: countries with negative net revenue.
- monthly_revenue: revenue in one month.
- month_comparison: compare revenue across two months.
- general_explanation: conceptual analytics questions.
- unsupported: other questions not covered above.
- month and comparison_month are full English month names or null.
- year and comparison_year are four-digit years or null.
- direction is highest or lowest when relevant, otherwise null.
- Do not answer the question; only classify it.
"""
    try:
        raw = _call_llm([
            {"role": "system", "content": instructions},
            {"role": "user", "content": q},
        ])
        intent_data = json.loads(raw)
    except (requests.RequestException, ValueError, KeyError):
        return "I couldn't interpret the question using the local LLM. Please try rephrasing it."

    intent = intent_data.get("intent")
    month = intent_data.get("month")
    year = str(intent_data.get("year") or "2011")
    comparison_month = intent_data.get("comparison_month")
    comparison_year = str(intent_data.get("comparison_year") or year)
    direction = intent_data.get("direction")

    month_numbers = {
        "january": "01", "february": "02", "march": "03",
        "april": "04", "may": "05", "june": "06",
        "july": "07", "august": "08", "september": "09",
        "october": "10", "november": "11", "december": "12",
    }

    def valid_month(value, selected_year):
        if not isinstance(value, str) or value.lower() not in month_numbers:
            return None
        if str(selected_year) not in {"2010", "2011"}:
            return None
        return f"{selected_year}-{month_numbers[value.lower()]}"

    try:
        if intent == "country_ranking":
            selected_month = valid_month(month, year)
            if selected_month:
                data = analytics.run_query(
                    """
                    SELECT Country, ROUND(SUM(Revenue), 2) AS net_revenue
                    FROM retail_sales
                    WHERE STRFTIME(InvoiceDate, '%Y-%m') = ? AND Country IS NOT NULL
                    GROUP BY Country ORDER BY net_revenue
                    """,
                    [selected_month],
                )
                if data.empty:
                    return f"No country data was found for {selected_month}."
                result = data.iloc[0] if direction == "lowest" else data.iloc[-1]
                period = f"in {selected_month}"
            else:
                data = analytics.get_top_countries("2010-12", "2011-12", 100)
                if data.empty:
                    return "No country revenue data was found."
                result = data.sort_values("net_revenue").iloc[0] if direction == "lowest" else data.sort_values("net_revenue", ascending=False).iloc[0]
                period = "across the dataset period"
            return (
                f"{result['Country']} had the {direction or 'highest'} net revenue "
                f"{period}: £{result['net_revenue']:,.2f}. Net revenue includes negative line values."
            )

        if intent == "negative_countries":
            selected_month = valid_month(month, year)
            if not selected_month:
                return "Please specify a month, such as January 2011."
            data = analytics.run_query(
                """
                SELECT Country, ROUND(SUM(Revenue), 2) AS net_revenue
                FROM retail_sales
                WHERE STRFTIME(InvoiceDate, '%Y-%m') = ? AND Country IS NOT NULL
                GROUP BY Country HAVING SUM(Revenue) < 0 ORDER BY net_revenue
                """,
                [selected_month],
            )
            if data.empty:
                return f"No countries had negative net revenue in {selected_month}."
            return "Countries with negative net revenue:\n" + "\n".join(
                f"{r.Country}: £{r.net_revenue:,.2f}" for r in data.itertuples(index=False)
            )

        if intent == "monthly_revenue":
            selected_month = valid_month(month, year)
            if not selected_month:
                return "Please specify a month and year, for example January 2011."
            data = analytics.get_monthly_revenue(selected_month, selected_month)
            if data.empty:
                return f"No revenue data was found for {selected_month}."
            return f"Net revenue for {selected_month} was £{data.iloc[0]['net_revenue']:,.2f}."

        if intent == "month_comparison":
            first = valid_month(month, year)
            second = valid_month(comparison_month, comparison_year)
            if not first or not second:
                return "Please specify both months, for example January and February 2011."
            data = analytics.run_query(
                """
                SELECT STRFTIME(InvoiceDate, '%Y-%m') AS month,
                       ROUND(SUM(Revenue), 2) AS net_revenue
                FROM retail_sales
                WHERE STRFTIME(InvoiceDate, '%Y-%m') IN (?, ?)
                GROUP BY STRFTIME(InvoiceDate, '%Y-%m')
                """,
                [first, second],
            )
            values = dict(zip(data["month"], data["net_revenue"]))
            if first not in values or second not in values:
                return "One or both selected months have no revenue data."
            diff = values[second] - values[first]
            return (
                f"{first}: £{values[first]:,.2f}\n{second}: £{values[second]:,.2f}\n"
                f"Change from {first} to {second}: £{diff:,.2f}."
            )

        if intent == "general_explanation":
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": (
                            "You are a clear business analytics tutor. Explain concepts "
                            "concisely. Never claim to have queried the dataset unless "
                            "results were supplied. Label hypothetical examples."
                        )},
                        {"role": "user", "content": q},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=180,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

        return (
            "I can't answer that question with the current analytics yet. Try asking "
            "about product opportunities by country, country revenue, negative-revenue "
            "countries, monthly revenue, or comparing two months."
        )

    except requests.RequestException:
        return "The local LLM service is unavailable. Check that Ollama is running."
    except (ValueError, KeyError, TypeError) as exc:
        return f"I couldn't process that question: {exc}"
