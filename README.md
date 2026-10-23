# Maison & Mercantile --- Commercial Intelligence Platform

A portfolio project exploring retail performance through interactive
business analytics. The dashboard brings together sales trends, product
rankings, market comparisons, transaction diagnostics, and a
natural-language question interface.

> **Project context:** Maison & Mercantile is a fictional
> retail-business scenario built for portfolio demonstration. The
> analysis uses the public [UCI Online Retail
> dataset](https://archive.ics.uci.edu/dataset/352/online+retail). It
> does not represent a real company.

## Overview

The Streamlit application helps users explore historical retail
transactions and answer questions such as: - How does net line revenue
change over time? - Which products generate the highest positive sales
value? - Which countries lead by net line revenue? - How do positive
line sales, negative line value, and net line revenue compare? - Which
countries have negative net line revenue in a selected period? - What
patterns should be investigated further?

## Dashboard pages

-   **Executive Overview** --- headline KPIs, monthly revenue trend,
    country distribution, product and market rankings, and commercial
    opportunities.
-   **Product Intelligence** --- product rankings, product snapshots,
    and product-level detail.
-   **Market Intelligence** --- country-level comparisons, map, and
    market leaderboard.
-   **Sales Diagnostics** --- positive line sales, negative line value,
    and net line revenue.
-   **Maison Intelligence** --- natural-language questions for supported
    business-analysis queries.
-   **Data & Methodology** --- data source, metric definitions, and
    interpretation limitations.

## Technology

-   Python --- application and analysis logic
-   Streamlit --- interactive dashboard UI
-   DuckDB --- analytical SQL queries
-   Pandas --- tabular data handling
-   Plotly --- interactive charts and maps
-   Ollama --- optional local language-model integration

The current AI integration is configured for the local Ollama endpoint
`http://localhost:11434/api/chat` and model `qwen2.5:3b`. It requires
Ollama to be installed, the model downloaded, and the service running.

## Data source

The project uses the UCI Machine Learning Repository's **Online Retail**
dataset, containing historical transactional records from a UK-based
online retailer.

The cleaned project data contains approximately **534,129 transaction
lines**, covering **2010-12-01 through 2011-12-09**. December 2011 is
incomplete and should not be compared with complete months without this
caveat.

The app expects a DuckDB database named `business_analytics.duckdb`
alongside `app.py`, containing a table named `retail_sales`.

## Metric definitions

-   **Positive line sales (£):** sum of `Quantity × UnitPrice` for rows
    with positive quantity.
-   **Negative line value (£):** absolute value of the summed
    `Quantity × UnitPrice` for rows with negative quantity.
-   **Net line revenue (£):** positive line sales minus negative line
    value.
-   **Positive units sold:** sum of quantities from rows with positive
    quantity.
-   **Order activity:** a proxy based on non-cancellation invoice IDs,
    as defined in the application.
-   **Identified customers:** distinct non-missing customer IDs.

### Important interpretation limits

-   **Revenue is not profit.** The dataset does not provide product
    costs or margins, so profit, gross margin, and ROI cannot be
    calculated reliably.
-   Negative quantities may reflect returns, cancellations, or
    adjustments; they are **not a verified returns-only measure**.
-   Invoice IDs are an order-activity proxy, not necessarily a perfect
    count of completed customer orders.
-   Product rankings based on positive sales are not the same as
    rankings by net line revenue. A product can have high positive sales
    and an offsetting negative line value.
-   The dataset is historical and ends on 2011-12-09. Do not present
    findings as current market facts.
-   Maison & Mercantile and its branding are fictional.

## Run locally

### 1. Install dependencies

If the project contains a `requirements.txt`, run:

``` bash
pip install -r requirements.txt
```

Otherwise, install the core packages used by the dashboard:

``` bash
pip install streamlit duckdb pandas plotly
```

For the optional AI feature, install [Ollama](https://ollama.com/), then
pull the configured model:

``` bash
ollama pull qwen2.5:3b
```

### 2. Check project files

Keep the main application files together:

``` text
AI-Business-Analyst-Assistant/
├── app.py
├── analytics.py
├── llm_service.py
├── business_analytics.duckdb
└── README.md
```

The project may contain additional data or configuration files. Unless
the code has been changed, the app expects `business_analytics.duckdb`
next to `app.py`.

### 3. Start Streamlit

From the project directory, run:

``` bash
python -m streamlit run app.py
```

For example, in Windows Command Prompt:

``` bat
cd "%USERPROFILE%\OneDrive\Documents\AI-Business-Analyst-Assistant"
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, commonly
`http://localhost:8501`.

### 4. Use the dashboard

1.  Select a reporting start month and end month in the sidebar.
2.  Choose a country or **All countries**.
3.  Explore the six pages using sidebar navigation.
4.  On Maison Intelligence, ask a question supported by the analysis
    functions. The local Ollama service must be running for model-backed
    responses.

## Validation checklist

-   Change the country filter and confirm relevant results update.
-   Select one month, such as January 2011, and confirm the charts and
    reporting period update.
-   Check that positive line sales minus negative line value equals net
    line revenue.
-   Keep the December 2011 partial-month caveat in mind.
-   Test each dashboard page and the AI feature separately.
-   Check that AI failures produce a clear message or fallback rather
    than a misleading answer.

## Screenshots

Before publishing, add screenshots for the Executive Overview, Product
Intelligence, Market Intelligence, Sales Diagnostics, Maison
Intelligence, and Data & Methodology pages. Store them in a
`screenshots/` folder, then reference them like this:

``` markdown
![Executive Overview](screenshots/executive-overview.png)
```

Only publish screenshots that do not expose private paths, credentials,
personal data, or local machine details.

## Repository hygiene

-   Never commit API keys, passwords, tokens, or private configuration.
-   Avoid committing large database files unless you intend to
    distribute them and have checked repository limits and dataset
    terms.
-   If the database is excluded, explain how to obtain the public
    dataset and recreate the local DuckDB database.
-   Include a `requirements.txt`.
-   Test setup instructions in a clean environment if possible.

## Portfolio summary

**Maison & Mercantile** is an interactive retail analytics dashboard
built with Python, Streamlit, DuckDB, Pandas, and Plotly. It explores
historical transaction data through KPI reporting, product and country
rankings, revenue diagnostics, and an optional local LLM-powered
natural-language interface. The project emphasizes transparent metric
definitions and responsible interpretation of revenue, negative-quantity
transactions, and incomplete reporting periods.

## Credits

-   Dataset: UCI Machine Learning Repository, Online Retail.
-   Dashboard framework: Streamlit.
-   Analytical database: DuckDB.
-   Visualization library: Plotly.
-   Optional local model runtime: Ollama.
