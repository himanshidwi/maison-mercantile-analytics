from pathlib import Path
import calendar
import html

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from llm_service import ask_llm
except Exception:
    ask_llm = None

# Maison & Mercantile | Retail Intelligence
st.set_page_config(
    page_title="Maison & Mercantile | Commercial Intelligence",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "business_analytics.duckdb"

# Brand palette: dark maroon, burgundy, warm ivory, muted rose.
MAROON = "#35111D"
BURGUNDY = "#672238"
BURGUNDY_2 = "#85364D"
ROSE = "#B77A86"
PALE_ROSE = "#F0DFE0"
IVORY = "#F7F2EC"
PANEL = "#FFFCF8"
BORDER = "#E7DCD5"
INK = "#2C2426"
MUTED = "#7B6D6D"
GREEN = "#587A63"
RED = "#A34E55"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@400;500;600&display=swap');
:root {{
 --bg:{IVORY}; --panel:{PANEL}; --border:{BORDER}; --ink:{INK}; --muted:{MUTED};
 --maroon:{MAROON}; --burgundy:{BURGUNDY}; --rose:{ROSE};
}}
html, body, [data-testid="stAppViewContainer"] {{
 background:var(--bg); color:var(--ink); font-family:'DM Sans',sans-serif;
}}
[data-testid="stHeader"] {{ background:rgba(247,242,236,.96); }}
[data-testid="stAppViewContainer"] .main .block-container {{
 max-width:1600px; padding:1.15rem 1.65rem 2.2rem;
}}
[data-testid="stSidebar"] {{
 background:linear-gradient(180deg,{MAROON} 0%,#421625 58%,#2C1019 100%);
 border-right:1px solid #5A2A39;
}}
[data-testid="stSidebar"] > div:first-child {{ padding:1.2rem .9rem 1.3rem; }}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {{ color:#E5D4D7 !important; }}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] strong {{ color:#FFF9F4 !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
 background:#512333;border-color:#744251;color:#FFF9F4;
}}
[data-testid="stSidebar"] [data-baseweb="select"] * {{ color:#FFF9F4 !important; }}
h1,h2,h3,h4 {{ color:var(--ink) !important; font-family:'Playfair Display',Georgia,serif !important; letter-spacing:-.025em; }}
p,li,label {{ color:#6F6061; }}
.brand-monogram {{
 font-family:'Playfair Display',Georgia,serif; color:#FFF5EE; font-size:2.3rem;
 text-align:center; letter-spacing:.12em; line-height:1.05; margin-top:.2rem;
}}
.brand-name {{
 font-family:'Playfair Display',Georgia,serif; color:#FFF5EE; font-size:1.1rem;
 letter-spacing:.11em; line-height:1.35; text-align:center; margin-top:.5rem;
}}
.brand-tagline {{ color:#D9B8C0; text-align:center; font-size:.64rem; letter-spacing:.22em; margin:.5rem 0 1.4rem; }}
.sidebar-nav-note {{ color:#D5B6BF; text-transform:uppercase; font-size:.62rem; letter-spacing:.16em; margin:.8rem 0 .25rem; }}
.hero {{
 background:linear-gradient(112deg,{MAROON} 0%,#4B1728 68%,#62263A 100%);
 border-radius:12px; padding:1.7rem 1.9rem 1.55rem; color:#FFF8F2;
 margin-bottom:1rem; position:relative; overflow:hidden;
 border:1px solid #5B2A3A;
}}
.hero:after {{
 content:'M  M'; position:absolute; right:2rem; top:1.2rem; font-family:'Playfair Display',Georgia,serif;
 font-size:5rem; color:rgba(255,240,233,.055); letter-spacing:.08em; pointer-events:none;
}}
.hero-kicker {{ text-transform:uppercase; font-size:.66rem; letter-spacing:.22em; color:#DDBFC5; margin-bottom:.6rem; }}
.hero-title {{ font-family:'Playfair Display',Georgia,serif; font-size:clamp(2rem,3.3vw,3.25rem); line-height:1.05; color:#FFF8F2; margin:0 0 .65rem; }}
.hero-subtitle {{ color:#E7D5D8; font-size:.94rem; max-width:700px; line-height:1.6; }}
.hero-period {{ border-left:1px solid #865666; padding-left:1rem; margin-left:1rem; }}
.hero-period-label {{ color:#DDBFC5; text-transform:uppercase; letter-spacing:.14em; font-size:.63rem; }}
.hero-period-value {{ color:#FFF8F2; font-size:.88rem; margin-top:.4rem; line-height:1.6; }}
.section-kicker {{ color:{BURGUNDY}; text-transform:uppercase; letter-spacing:.16em; font-weight:700; font-size:.65rem; margin:.8rem 0 .25rem; }}
.section-note {{ color:{MUTED}; font-size:.82rem; margin-top:-.45rem; margin-bottom:.8rem; line-height:1.5; }}
.metric-card {{
 background:var(--panel); border:1px solid var(--border); border-radius:10px;
 padding:1rem 1.05rem .9rem; min-height:126px; box-shadow:0 4px 16px rgba(61,25,37,.035);
}}
.metric-top {{ display:flex; align-items:center; gap:.65rem; margin-bottom:.65rem; }}
.metric-icon {{ display:flex; align-items:center; justify-content:center; width:38px; height:38px;
 background:{PALE_ROSE}; border-radius:50%; color:{BURGUNDY}; font-size:1.1rem; flex-shrink:0; }}
.metric-label {{ color:{BURGUNDY}; text-transform:uppercase; letter-spacing:.10em; font-size:.64rem; font-weight:700; }}
.metric-value {{ color:{MAROON}; font-family:'Playfair Display',Georgia,serif; font-size:clamp(1.45rem,2vw,2rem); line-height:1.1; white-space:nowrap; }}
.metric-foot {{ color:{MUTED}; font-size:.7rem; margin-top:.55rem; line-height:1.4; }}
.panel {{
 background:{PANEL}; border:1px solid {BORDER}; border-radius:10px; padding:1rem 1.05rem .8rem;
 box-shadow:0 4px 16px rgba(61,25,37,.025); height:100%;
}}
.panel-title {{ color:{MAROON}; font-family:'Playfair Display',Georgia,serif; font-size:1.23rem; margin:0 0 .15rem; }}
.panel-subtitle {{ color:{MUTED}; font-size:.74rem; margin-bottom:.6rem; line-height:1.4; }}
.rank-row {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:.7rem; align-items:center;
 padding:.62rem 0; border-bottom:1px solid #EEE5DF; }}
.rank-row:last-child {{ border-bottom:none; }}
.rank-name {{ color:{INK}; font-size:.78rem; line-height:1.35; overflow-wrap:anywhere; }}
.rank-value {{ color:{BURGUNDY}; font-size:.78rem; font-weight:700; text-align:right; white-space:nowrap; }}
.rank-track {{ background:#F0E7E2; height:4px; border-radius:99px; overflow:hidden; margin-top:.4rem; }}
.rank-fill {{ background:{BURGUNDY}; height:100%; border-radius:99px; }}
.insight-card {{ background:{PANEL}; border:1px solid {BORDER}; border-left:3px solid {ROSE}; border-radius:8px; padding:.9rem 1rem; min-height:115px; }}
.insight-label {{ color:{BURGUNDY}; text-transform:uppercase; letter-spacing:.1em; font-size:.62rem; font-weight:700; margin-bottom:.45rem; }}
.insight-text {{ color:{INK}; font-size:.82rem; line-height:1.55; }}
.feature-card {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:10px; padding:1rem; height:156px; box-sizing:border-box; display:flex; flex-direction:column; }}
.feature-icon {{ width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:{PALE_ROSE};color:{BURGUNDY};font-size:1rem;margin-bottom:.7rem; }}
.feature-title {{ font-family:'Playfair Display',Georgia,serif; color:{MAROON}; font-size:1.05rem; margin-bottom:.35rem; }}
.feature-copy {{ color:{MUTED}; font-size:.78rem; line-height:1.5; }}
.st-key-goto_products button, .st-key-goto_markets button, .st-key-goto_ai button {{ min-height:48px; height:48px; }}
div[data-testid="stPlotlyChart"] {{ background:transparent; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:10px; box-shadow:0 4px 16px rgba(61,25,37,.025); }}
div[data-testid="stVerticalBlockBorderWrapper"] > div {{ padding:1rem 1.05rem .85rem; }}
div[data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:8px; overflow:hidden; }}
div[data-baseweb="select"] > div {{ background:{PANEL}; border-color:#DCCBC6; border-radius:7px; }}
input,textarea {{ background:{PANEL} !important; border-color:#DCCBC6 !important; color:{INK} !important; border-radius:7px !important; }}
.stButton > button {{ background:{BURGUNDY}; color:#FFF8F2; border:1px solid {BURGUNDY}; border-radius:7px; font-weight:600; }}
.stButton > button:hover {{ background:{MAROON}; border-color:{MAROON}; color:#FFF8F2; }}
div[data-testid="stAlert"] {{ border-radius:8px; }}
hr {{ border-color:{BORDER}; }}
.footer {{ color:#9B8988; text-align:center; letter-spacing:.12em; font-size:.62rem; padding:1rem 0 .2rem; }}
@media(max-width:900px) {{
 [data-testid="stAppViewContainer"] .main .block-container {{ padding:.7rem .75rem 1.4rem; }}
 .hero {{ padding:1.2rem; }}
 .hero-period {{ border-left:none; margin-left:0; padding-left:0; margin-top:.8rem; }}
}}
</style>
""", unsafe_allow_html=True)

def query(sql, params=None):
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Keep business_analytics.duckdb beside app.py."
        )
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(sql, params or []).df()

@st.cache_data(ttl=300, show_spinner=False)
def load_metadata(db_path):
    with duckdb.connect(db_path, read_only=True) as con:
        months = con.execute("""
            SELECT DISTINCT STRFTIME(InvoiceDate, '%Y-%m') AS month
            FROM retail_sales WHERE InvoiceDate IS NOT NULL ORDER BY month
        """).df()["month"].tolist()
        countries = con.execute("""
            SELECT DISTINCT Country FROM retail_sales
            WHERE Country IS NOT NULL ORDER BY Country
        """).df()["Country"].tolist()
        meta = con.execute("""
            SELECT COUNT(*) AS rows, MIN(InvoiceDate) AS min_date, MAX(InvoiceDate) AS max_date
            FROM retail_sales
        """).df().iloc[0]
    return months, countries, int(meta["rows"]), meta["min_date"], meta["max_date"]

def money(v):
    if v is None or pd.isna(v):
        return "—"
    v = float(v)
    if abs(v) >= 1_000_000:
        return f"£{v/1_000_000:,.2f}M"
    if abs(v) >= 10_000:
        return f"£{v/1_000:,.1f}K"
    return f"£{v:,.0f}"

def period_text(start, end):
    a = pd.to_datetime(start + "-01").strftime("%d %b %Y")
    bdate = pd.to_datetime(end + "-01") + pd.offsets.MonthEnd(0)
    # Dataset boundary is partial; actual max date is shown separately in source note.
    b = bdate.strftime("%d %b %Y")
    return f"{a} – {b}"

def month_shift(month, offset):
    year, mon = map(int, month.split("-"))
    idx = year * 12 + mon - 1 + offset
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"

def plot_theme(fig, height=330):
    fig.update_layout(
        height=height, autosize=True, margin=dict(l=8, r=8, t=12, b=12),
        paper_bgcolor=PANEL, plot_bgcolor=PANEL,
        font=dict(family="DM Sans, Arial, sans-serif", color=MUTED, size=10),
        hoverlabel=dict(bgcolor=MAROON, bordercolor=BURGUNDY, font=dict(color="#FFF8F2")),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=BORDER, zeroline=False,
                     tickfont=dict(color=MUTED, size=10))
    fig.update_yaxes(showgrid=True, gridcolor="#F0E7E2", showline=False, zeroline=False,
                     tickfont=dict(color=MUTED, size=10))
    return fig

def metric(col, icon, label, value, foot):
    col.markdown(f"""
    <div class="metric-card">
      <div class="metric-top"><div class="metric-icon">{icon}</div><div class="metric-label">{label}</div></div>
      <div class="metric-value">{value}</div><div class="metric-foot">{foot}</div>
    </div>""", unsafe_allow_html=True)

def rank_panel(df, name_col, value_col, value_format=money, limit=5):
    if df.empty:
        st.caption("No results for the selected period.")
        return
    rows = df.head(limit)
    maxval = max(float(rows[value_col].abs().max()), 1)
    for _, row in rows.iterrows():
        name = html.escape(str(row[name_col]))
        val = float(row[value_col])
        width = max(0, min(100, abs(val) / maxval * 100))
        st.markdown(f"""
        <div class="rank-row">
          <div><div class="rank-name">{name}</div>
          <div class="rank-track"><div class="rank-fill" style="width:{width:.1f}%"></div></div></div>
          <div class="rank-value">{value_format(val)}</div>
        </div>""", unsafe_allow_html=True)

# Sidebar identity and navigation
try:
    months, countries, total_rows, min_date, max_date = load_metadata(str(DB_PATH))
except Exception as exc:
    st.error(f"Unable to load the retail database: {exc}")
    st.stop()
if not months:
    st.error("The retail_sales table has no dated transactions.")
    st.stop()

with st.sidebar:
    st.markdown('<div class="brand-monogram">M | M</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-name">MAISON &<br>MERCANTILE</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-tagline">HOME · GIFTS · LIFESTYLE</div>', unsafe_allow_html=True)
    st.divider()
    page = st.radio(
        "WORKSPACE",
        ["Executive Overview", "Product Intelligence", "Market Intelligence",
         "Sales Diagnostics", "Maison Intelligence", "Data & Methodology"],
        label_visibility="visible",
        key="page_navigation",
    )
    st.divider()
    st.markdown('<div class="sidebar-nav-note">REPORTING PERIOD</div>', unsafe_allow_html=True)
    start_month = st.selectbox("From month", months, index=0, key="start_month")
    end_month = st.selectbox("To month", months, index=len(months)-1, key="end_month")
    selected_country = st.selectbox("Country", ["All countries"] + countries, index=0, key="selected_country")
    st.divider()
    st.caption(f"{total_rows:,} cleaned transaction lines")
    st.caption(f"Source data: {pd.to_datetime(min_date).date()} – {pd.to_datetime(max_date).date()}")
    st.caption("Currency: GBP (£)")
    st.caption("Public source: UCI Online Retail")

if start_month > end_month:
    st.error("The end month must be on or after the start month.")
    st.stop()

start_date = f"{start_month}-01"
end_exclusive = f"{month_shift(end_month, 1)}-01"
scope_where = "InvoiceDate >= CAST(? AS DATE) AND InvoiceDate < CAST(? AS DATE)"
scope_params = [start_date, end_exclusive]
if selected_country != "All countries":
    scope_where += " AND Country = ?"
    scope_params.append(selected_country)

scope_label = f"{pd.to_datetime(start_month+'-01').strftime('%b %Y')} – {pd.to_datetime(end_month+'-01').strftime('%b %Y')}"
country_label = selected_country if selected_country != "All countries" else "All markets"

# Hero header
if page == "Executive Overview":
    hero_title = "Your business, in focus."
    hero_subtitle = "Sales performance, product insights and international market opportunities."
elif page == "Product Intelligence":
    hero_title = "Understand your product mix."
    hero_subtitle = "Explore product performance, demand signals and items worth investigating."
elif page == "Market Intelligence":
    hero_title = "See opportunity across markets."
    hero_subtitle = "Compare country performance and explore where products find demand."
elif page == "Sales Diagnostics":
    hero_title = "Investigate the signals."
    hero_subtitle = "Monitor revenue movement, negative transaction values and data-quality considerations."
elif page == "Maison Intelligence":
    hero_title = "Ask better business questions."
    hero_subtitle = "Explore the retail data in plain English with evidence from analytical queries."
else:
    hero_title = "Know how the numbers work."
    hero_subtitle = "Metric definitions, data coverage and important limitations."
st.markdown(f"""
<div class="hero">
 <div class="hero-kicker">Maison & Mercantile · Commercial Intelligence Platform</div>
 <div class="hero-title">{hero_title}</div>
 <div class="hero-subtitle">{hero_subtitle}</div>
 <div style="margin-top:1rem;display:flex;gap:2rem;flex-wrap:wrap;">
  <div><div class="hero-period-label">Reporting period</div><div class="hero-period-value">{scope_label}<br><span style="color:#DDBFC5;font-size:.72rem;">Historical public dataset</span></div></div>
  <div><div class="hero-period-label">Market scope</div><div class="hero-period-value">{html.escape(country_label)}</div></div>
 </div>
</div>
""", unsafe_allow_html=True)

# Shared queries
kpi = query(f"""
SELECT
 COALESCE(SUM(Revenue),0) AS net_revenue,
 COALESCE(SUM(CASE WHEN Quantity > 0 THEN Revenue ELSE 0 END),0) AS positive_sales,
 COALESCE(-SUM(CASE WHEN Quantity < 0 THEN Revenue ELSE 0 END),0) AS negative_value,
 COUNT(DISTINCT CASE WHEN NOT STARTS_WITH(CAST(InvoiceNo AS VARCHAR),'C') THEN InvoiceNo END) AS invoice_count,
 COUNT(DISTINCT CustomerID) AS customers,
 COALESCE(SUM(CASE WHEN Quantity > 0 THEN Quantity ELSE 0 END),0) AS units_sold,
 COUNT(DISTINCT StockCode) AS products
FROM retail_sales WHERE {scope_where}
""", scope_params).iloc[0]

monthly = query(f"""
SELECT STRFTIME(InvoiceDate,'%Y-%m') AS month,
 SUM(Revenue) AS net_revenue,
 SUM(CASE WHEN Quantity > 0 THEN Revenue ELSE 0 END) AS positive_sales,
 -SUM(CASE WHEN Quantity < 0 THEN Revenue ELSE 0 END) AS negative_value
FROM retail_sales WHERE {scope_where}
GROUP BY 1 ORDER BY 1
""", scope_params)

market_params = [start_date, end_exclusive]
market_where = "InvoiceDate >= CAST(? AS DATE) AND InvoiceDate < CAST(? AS DATE)"
market = query(f"""
SELECT Country, SUM(Revenue) AS net_revenue,
 SUM(CASE WHEN Quantity > 0 THEN Revenue ELSE 0 END) AS positive_sales,
 COUNT(DISTINCT CASE WHEN NOT STARTS_WITH(CAST(InvoiceNo AS VARCHAR),'C') THEN InvoiceNo END) AS invoice_count,
 COUNT(DISTINCT CustomerID) AS customers,
 SUM(CASE WHEN Quantity > 0 THEN Quantity ELSE 0 END) AS units_sold
FROM retail_sales WHERE {market_where} AND Country IS NOT NULL
GROUP BY Country ORDER BY net_revenue DESC
""", market_params)

product_params = scope_params.copy()
products = query(f"""
SELECT Description AS product,
 SUM(Revenue) AS net_revenue,
 SUM(CASE WHEN Quantity > 0 THEN Revenue ELSE 0 END) AS positive_sales,
 -SUM(CASE WHEN Quantity < 0 THEN Revenue ELSE 0 END) AS negative_value,
 SUM(CASE WHEN Quantity > 0 THEN Quantity ELSE 0 END) AS units_sold,
 COUNT(DISTINCT InvoiceNo) AS invoice_ids,
 COUNT(DISTINCT CustomerID) AS identified_customers
FROM retail_sales WHERE {scope_where} AND Description IS NOT NULL
GROUP BY Description ORDER BY positive_sales DESC LIMIT 100
""", product_params)

# Mark partial boundary months, exclude from MoM growth.
if not monthly.empty:
    monthly["month_start"] = pd.to_datetime(monthly["month"] + "-01")
    monthly["previous_revenue"] = monthly["net_revenue"].shift(1)
    denom = monthly["previous_revenue"].abs().replace(0, float("nan"))
    monthly["mom_pct"] = (monthly["net_revenue"] - monthly["previous_revenue"]) / denom * 100
    source_start, source_end = pd.to_datetime(min_date), pd.to_datetime(max_date)
    partial = set()
    if source_start.day > 1:
        partial.add(source_start.strftime("%Y-%m"))
    if source_end.day < calendar.monthrange(source_end.year, source_end.month)[1]:
        partial.add(source_end.strftime("%Y-%m"))
    monthly.loc[monthly["month"].isin(partial), "mom_pct"] = float("nan")
else:
    partial = set()

if page == "Executive Overview":
    # KPI row
    st.markdown('<div class="section-kicker">01 / Executive summary</div>', unsafe_allow_html=True)
    cols = st.columns(4, gap="medium")
    metric(cols[0], "▥", "NET REVENUE", money(kpi["net_revenue"]), "Quantity × unit price, net of negative lines")
    metric(cols[1], "▣", "ORDER ACTIVITY", f'{int(kpi["invoice_count"]):,}', "Non-cancel invoice IDs; order proxy")
    metric(cols[2], "♙", "IDENTIFIED CUSTOMERS", f'{int(kpi["customers"]):,}', "Distinct non-missing customer IDs")
    metric(cols[3], "◇", "POSITIVE UNITS SOLD", f'{int(kpi["units_sold"]):,}', "Units on positive-quantity lines")
    st.caption("Revenue is not profit. Invoice IDs are a proxy for order activity, and negative line value may include returns or adjustments.")
    st.write("")

    st.markdown('<div class="section-kicker">02 / Performance at a glance</div>', unsafe_allow_html=True)
    # Row one contains only the two visualisations. Keep ranking cards in a separate row below.
    chart_left, chart_right = st.columns([1, 1], gap="medium")
    with chart_left:
        with st.container(border=True):
            st.markdown("<div class=\"panel-title\">Revenue trend</div>", unsafe_allow_html=True)
            st.markdown("<div class=\"panel-subtitle\">Monthly net line revenue across the selected period</div>", unsafe_allow_html=True)
            if not monthly.empty:
                fig = go.Figure()
                month_labels = pd.to_datetime(monthly["month"]).dt.strftime("%b %Y").tolist()
                # Mark partial source-boundary months so lower values are not mistaken for complete months.
                month_labels = [label + "*" if month in partial else label
                                for label, month in zip(month_labels, monthly["month"].tolist())]
                fig.add_trace(go.Scatter(
                    x=monthly["month"], y=monthly["net_revenue"], mode="lines+markers",
                    line=dict(color=BURGUNDY, width=3), marker=dict(size=6, color=BURGUNDY),
                    fill="tozeroy", fillcolor="rgba(103,34,56,.12)",
                    customdata=monthly[["positive_sales", "negative_value"]],
                    hovertemplate="<b>%{x}</b><br>Net revenue: £%{y:,.2f}<br>Positive sales: £%{customdata[0]:,.2f}<br>Negative line value: £%{customdata[1]:,.2f}<extra></extra>"
                ))
                fig.update_layout(height=330, margin=dict(l=4,r=8,t=8,b=8), paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                                  font=dict(color=MUTED,size=10), showlegend=False)
                fig.update_xaxes(type="category", tickmode="array", tickvals=monthly["month"].tolist(),
                                 ticktext=month_labels, tickangle=-25, showgrid=False, linecolor=BORDER)
                fig.update_yaxes(tickprefix="£", tickformat="~s", gridcolor="#F0E7E2", zeroline=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False}, key="overview_revenue_trend")
                if partial:
                    st.caption("* Partial month based on the available source-data date coverage.")
            else:
                st.info("No monthly revenue data for this selection.")

    with chart_right:
        with st.container(border=True):
            st.markdown("<div class=\"panel-title\">Revenue by country</div>", unsafe_allow_html=True)
            st.markdown("<div class=\"panel-subtitle\">Worldwide distribution · hover for exact values</div>", unsafe_allow_html=True)
            if not market.empty:
                map_data = market.copy()
                fig_map = px.choropleth(
                    map_data, locations="Country", locationmode="country names", color="net_revenue",
                    color_continuous_scale=[[0, "#F1E2E1"], [.35, "#C68D98"], [.7, "#8A3D53"], [1, MAROON]],
                    hover_name="Country", hover_data={"net_revenue":":,.2f", "Country":False},
                    labels={"net_revenue":"Net revenue (£)"}, projection="natural earth"
                )
                fig_map.update_geos(
                    showframe=False, showcoastlines=False, showcountries=True, countrycolor="#E4D8D3",
                    showland=True, landcolor="#F4EBE5", showocean=True, oceancolor=PANEL,
                    bgcolor=PANEL, projection_type="natural earth"
                )
                fig_map.update_layout(
                    height=330, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                    font=dict(color=MUTED,size=10), coloraxis_colorbar=dict(
                        title="", thickness=8, len=.65, tickfont=dict(size=9,color=MUTED), outlinewidth=0, x=1.0
                    )
                )
                st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar":False}, key="country_choropleth")
            else:
                st.info("No country data for this period.")

    st.markdown('<div class="section-kicker">03 / Commercial rankings</div>', unsafe_allow_html=True)
    rank_left, rank_right = st.columns([1, 1], gap="medium")
    with rank_left:
        with st.container(border=True):
            st.markdown("<div class=\"panel-title\">Products driving positive sales</div>", unsafe_allow_html=True)
            st.markdown("<div class=\"panel-subtitle\">Leading products by historical positive-quantity sales</div>", unsafe_allow_html=True)
            if not products.empty:
                rank_panel(products.sort_values("positive_sales", ascending=False), "product", "positive_sales", money, 5)
            else:
                st.caption("No product sales data for this period.")
    with rank_right:
        with st.container(border=True):
            st.markdown("<div class=\"panel-title\">Top markets by net revenue</div>", unsafe_allow_html=True)
            st.markdown("<div class=\"panel-subtitle\">Leading countries in the selected date range</div>", unsafe_allow_html=True)
            if not market.empty:
                rank_panel(market.head(5), "Country", "net_revenue", money, 5)
            else:
                st.caption("No country data for this period.")

    st.write("")
    st.markdown('<div class="section-kicker">04 / Commercial opportunities</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3,gap="medium")
    with c1:
        st.markdown('<div class="feature-card"><div class="feature-icon">◇</div><div class="feature-title">Product intelligence</div><div class="feature-copy">Identify products with strong historical sales and investigate changes in demand.</div></div>',unsafe_allow_html=True)
        st.button("Explore products →", key="goto_products", on_click=lambda: st.session_state.update(page_navigation="Product Intelligence"), use_container_width=True)
    with c2:
        st.markdown('<div class="feature-card"><div class="feature-icon">◎</div><div class="feature-title">Market intelligence</div><div class="feature-copy">Compare international markets and shortlist product-market combinations for research.</div></div>',unsafe_allow_html=True)
        st.button("Explore markets →", key="goto_markets", on_click=lambda: st.session_state.update(page_navigation="Market Intelligence"), use_container_width=True)
    with c3:
        st.markdown('<div class="feature-card"><div class="feature-icon">✧</div><div class="feature-title">Maison Intelligence</div><div class="feature-copy">Ask a business question in plain English and explore data-backed findings.</div></div>',unsafe_allow_html=True)
        st.button("Ask Maison AI →", key="goto_ai", on_click=lambda: st.session_state.update(page_navigation="Maison Intelligence"), use_container_width=True)

    st.markdown('<div class="section-kicker">05 / Signals worth investigating</div>', unsafe_allow_html=True)
    insights = []
    if not monthly.empty:
        complete_monthly = monthly[~monthly["month"].isin(partial)]
        signal_monthly = complete_monthly if not complete_monthly.empty else monthly
        high = signal_monthly.loc[signal_monthly["net_revenue"].idxmax()]
        low = signal_monthly.loc[signal_monthly["net_revenue"].idxmin()]
        insights.append(("HIGHEST REVENUE MONTH", f"{high['month']} recorded the highest monthly net revenue in this selection: {money(high['net_revenue'])}."))
        insights.append(("LOWEST REVENUE MONTH", f"{low['month']} recorded the lowest monthly net revenue in this selection: {money(low['net_revenue'])}."))
        growth = monthly.dropna(subset=["mom_pct"])
        if not growth.empty:
            decline = growth.loc[growth["mom_pct"].idxmin()]
            insights.append(("LARGEST MONTHLY DECLINE", f"{decline['month']} recorded a {decline['mom_pct']:.1f}% month-on-month change. This is a signal to investigate, not proof of cause."))
    if insights:
        for idx in range(0,len(insights),3):
            rowcols=st.columns(3,gap="medium")
            for col,item in zip(rowcols,insights[idx:idx+3]):
                col.markdown(f'<div class="insight-card"><div class="insight-label">{item[0]}</div><div class="insight-text">{html.escape(item[1])}</div></div>',unsafe_allow_html=True)

elif page == "Product Intelligence":
    st.markdown('<div class="section-kicker">01 / Product performance</div>', unsafe_allow_html=True)
    st.subheader("Products worth a closer look")
    st.markdown('<div class="section-note">Ranked by positive-quantity sales. Net revenue remains available in the detailed view because negative lines affect the final total.</div>', unsafe_allow_html=True)
    search = st.text_input("Find a product", placeholder="Search product description…")
    min_units = st.number_input("Minimum positive units sold", min_value=0, value=0, step=1)
    pview = products.copy()
    if search.strip():
        pview = pview[pview["product"].str.contains(search.strip(), case=False, na=False)]
    pview = pview[pview["units_sold"].fillna(0) >= min_units]
    top = pview.head(15).sort_values("positive_sales", ascending=True)
    a,b=st.columns([1,1],gap="medium")
    with a:
        with st.container(border=True):
            st.markdown("<div class=\"panel-title\">Top products by positive sales</div>", unsafe_allow_html=True)
            st.markdown("<div class=\"panel-subtitle\">Selected reporting period</div>", unsafe_allow_html=True)
            if not top.empty:
                fig=px.bar(top,x="positive_sales",y="product",orientation="h",color_discrete_sequence=[BURGUNDY],
                           labels={"positive_sales":"Positive sales (£)","product":""},hover_data={"units_sold":":,.0f","net_revenue":":,.2f"})
                fig.update_traces(hovertemplate="<b>%{y}</b><br>Positive sales: £%{x:,.2f}<extra></extra>",marker_line_width=0)
                fig.update_layout(height=470,margin=dict(l=5,r=8,t=8,b=8),paper_bgcolor=PANEL,plot_bgcolor=PANEL,font=dict(color=MUTED,size=10))
                fig.update_xaxes(tickprefix="£",tickformat="~s",gridcolor="#F0E7E2")
                fig.update_yaxes(showgrid=False,automargin=True)
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False},key="products_bar")
            else:
                st.info("No products match those filters.")

    with b:
        with st.container(border=True):
            st.markdown("<div class=\"panel-title\">Product snapshot</div>", unsafe_allow_html=True)
            st.markdown("<div class=\"panel-subtitle\">Leading items by historical positive sales</div>", unsafe_allow_html=True)
            rank_panel(pview.sort_values("positive_sales",ascending=False),"product","positive_sales",money,8)

    with st.expander("View product-level detail"):
        detail=pview.copy()
        detail=detail.rename(columns={"product":"Product","net_revenue":"Net revenue (£)","positive_sales":"Positive sales (£)","negative_value":"Negative line value (£)","units_sold":"Positive units sold","invoice_ids":"Invoice IDs","identified_customers":"Identified customers"})
        st.dataframe(detail,use_container_width=True,hide_index=True)
    st.info("Interpretation: historical sales and units can help prioritise investigation. The dataset does not include costs, stock availability, or future demand, so it cannot identify the most profitable product.")

elif page == "Market Intelligence":
    st.markdown('<div class="section-kicker">01 / International performance</div>', unsafe_allow_html=True)
    st.subheader("Revenue and activity by market")
    st.markdown('<div class="section-note">Country-level comparisons use all countries in the selected date range, independent of the single-country filter.</div>', unsafe_allow_html=True)
    left,right=st.columns([1,1],gap="medium")
    with left:
        with st.container(border=True):
            st.markdown("<div class=\"panel-title\">World revenue map</div>", unsafe_allow_html=True)
            st.markdown("<div class=\"panel-subtitle\">Darker burgundy indicates higher net revenue</div>", unsafe_allow_html=True)
            if not market.empty:
                fig=px.choropleth(market,locations="Country",locationmode="country names",color="net_revenue",
                    color_continuous_scale=[[0,"#F1E2E1"],[.35,"#C68D98"],[.7,"#8A3D53"],[1,MAROON]],
                    hover_name="Country",hover_data={"net_revenue":":,.2f"},labels={"net_revenue":"Net revenue (£)"},projection="natural earth")
                fig.update_geos(showframe=False,showcoastlines=False,showcountries=True,countrycolor="#E4D8D3",showland=True,landcolor="#F4EBE5",showocean=True,oceancolor=PANEL,bgcolor=PANEL)
                fig.update_layout(height=480,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor=PANEL,plot_bgcolor=PANEL,font=dict(color=MUTED,size=10),
                                  coloraxis_colorbar=dict(title="",thickness=9,tickfont=dict(size=9),outlinewidth=0))
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False},key="market_world_map")

    with right:
        with st.container(border=True):
            st.markdown("<div class=\"panel-title\">Market leaderboard</div>", unsafe_allow_html=True)
            st.markdown("<div class=\"panel-subtitle\">Ranked by net revenue</div>", unsafe_allow_html=True)
            rank_panel(market.head(12),"Country","net_revenue",money,12)

    st.write("")
    display=market.rename(columns={"Country":"Country","net_revenue":"Net revenue (£)","positive_sales":"Positive sales (£)","invoice_count":"Non-cancel invoice IDs","customers":"Identified customers","units_sold":"Positive units sold"})
    with st.expander("Explore all market metrics"):
        st.dataframe(display,use_container_width=True,hide_index=True)
    st.info("Use this ranking to shortlist markets for further research. Revenue alone does not establish market profitability, demand potential, or expansion readiness.")

elif page == "Sales Diagnostics":
    st.markdown('<div class="section-kicker">01 / Revenue composition</div>',unsafe_allow_html=True)
    st.subheader("Positive sales and negative line value")
    st.markdown('<div class="section-note">Negative quantities may reflect returns, cancellations or adjustments; they are not a verified returns-only measure.</div>',unsafe_allow_html=True)
    cols=st.columns(3,gap="medium")
    metric(cols[0],"＋","POSITIVE LINE SALES",money(kpi["positive_sales"]),"Positive-quantity line values")
    metric(cols[1],"−","NEGATIVE LINE VALUE",money(kpi["negative_value"]),"Absolute value of negative-quantity lines")
    metric(cols[2],"＝","NET LINE REVENUE",money(kpi["net_revenue"]),"Positive sales less negative line values")
    if not monthly.empty:
        diag=monthly.melt(id_vars="month",value_vars=["positive_sales","negative_value"],var_name="type",value_name="amount")
        diag["type"]=diag["type"].map({"positive_sales":"Positive sales","negative_value":"Negative line value"})
        fig=px.bar(diag,x="month",y="amount",color="type",barmode="group",
                   color_discrete_map={"Positive sales":BURGUNDY,"Negative line value":ROSE},
                   labels={"month":"Month","amount":"Value (£)","type":"Transaction value"})
        fig.update_layout(height=380,margin=dict(l=8,r=8,t=8,b=8),paper_bgcolor=PANEL,plot_bgcolor=PANEL,font=dict(color=MUTED,size=10),legend=dict(orientation="h",y=1.1))
        fig.update_xaxes(type="category",tickangle=-25,showgrid=False)
        fig.update_yaxes(tickprefix="£",tickformat="~s",gridcolor="#F0E7E2")
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False},key="diagnostic_composition")
    with st.expander("Monthly diagnostic table"):
        st.dataframe(monthly.rename(columns={"month":"Month","net_revenue":"Net revenue (£)","positive_sales":"Positive sales (£)","negative_value":"Negative line value (£)","mom_pct":"MoM change (%)"}),use_container_width=True,hide_index=True)
    st.markdown('<div class="section-kicker">02 / Data quality considerations</div>',unsafe_allow_html=True)
    st.markdown(f"""
    <div class="insight-card"><div class="insight-label">INTERPRETATION NOTE</div>
    <div class="insight-text">The selected period contains {int(kpi['products']):,} distinct stock codes and {int(kpi['customers']):,} identified customers. Missing customer IDs mean customer counts represent only identifiable customers. Product cost and margin data are not available, so profit cannot be calculated.</div></div>
    """,unsafe_allow_html=True)

elif page == "Maison Intelligence":
    st.markdown('<div class="section-kicker">01 / AI business analyst</div>',unsafe_allow_html=True)
    st.subheader("What would you like to understand?")
    st.markdown('<div class="section-note">Ask a business question. The local model interprets supported questions, and analytical figures come from DuckDB.</div>',unsafe_allow_html=True)
    prompts=[
        "Which country generated the highest revenue?",
        "Which products and markets should we investigate?",
        "Which countries had negative net revenue in January 2011?",
        "Compare January and February 2011 revenue.",
    ]
    with st.container(border=True):
        st.markdown("<div class=\"panel-title\">Suggested questions</div>", unsafe_allow_html=True)
        st.markdown("<div class=\"panel-subtitle\">Choose one to start exploring</div>", unsafe_allow_html=True)
        qcols=st.columns(2,gap="small")
        for i,prompt in enumerate(prompts):
            if qcols[i%2].button(prompt,key=f"suggested_{i}",use_container_width=True):
                st.session_state["maison_question"]=prompt

    question=st.text_area("Your question",key="maison_question",placeholder="e.g. Which product-market combinations should we investigate next quarter?",height=100)
    if st.button("Analyse question",key="maison_ask",use_container_width=True):
        if not question.strip():
            st.warning("Enter a question first.")
        elif ask_llm is None:
            st.error("The AI service could not be imported. Check that llm_service.py and its dependencies are present.")
        else:
            with st.spinner("Maison Intelligence is analysing your question…"):
                try:
                    answer=ask_llm(question.strip())
                    with st.container(border=True):
                        st.markdown("<div class=\"panel-title\">Maison Intelligence · Analysis</div>", unsafe_allow_html=True)
                        st.markdown(answer)

                except Exception as exc:
                    st.error(f"Could not get an answer from the local AI service: {exc}")
    st.caption("AI limitations: answers depend on supported question types and available data. Validate important decisions and do not infer profitability from revenue alone.")

elif page == "Data & Methodology":
    st.markdown('<div class="section-kicker">01 / Data provenance</div>',unsafe_allow_html=True)
    st.subheader("A transparent view of the numbers")
    cols=st.columns(3,gap="medium")
    metric(cols[0],"▤","TRANSACTION LINES",f"{total_rows:,}","Cleaned records in the local database")
    metric(cols[1],"◷","DATA COVERAGE",f"{pd.to_datetime(min_date).strftime('%b %Y')} – {pd.to_datetime(max_date).strftime('%b %Y')}","Observed transaction date range")
    metric(cols[2],"£","CURRENCY","GBP (£)","Amounts shown in British pounds")
    st.markdown("### Metric definitions")
    st.markdown("""
    - **Net line revenue:** sum of `Quantity × UnitPrice`, including negative quantities.
    - **Positive line sales:** sum of line values for rows with positive quantity.
    - **Negative line value:** absolute value of line values for rows with negative quantity. This may include returns, cancellations or adjustments.
    - **Order activity:** distinct invoice IDs not starting with `C`; a proxy, not proof of completed orders.
    - **Identified customers:** distinct non-missing `CustomerID` values.
    - **Positive units sold:** sum of positive quantities; negative quantities are excluded from this particular demand indicator.
    - **Profit:** cannot be calculated because product costs and margins are not included.
    - **Growth:** month-on-month comparisons exclude incomplete boundary months when identifiable from the source date coverage.
    """)
    st.markdown("### Business scenario")
    st.markdown("""
    **Maison & Mercantile is a fictional portfolio scenario**, used to frame a realistic retail commercial-intelligence use case. The transaction data is from the public UCI Online Retail dataset; it is not company-confidential data and does not represent real Maison & Mercantile operations.

    The platform demonstrates how a commercial team might explore historical product performance, market revenue, monthly movement and transaction-value signals. It supports investigation and prioritisation, not automatic investment decisions.
    """)
    st.markdown("### Known limitations")
    st.markdown("""
    - No product cost, gross margin, stock availability, advertising spend, shipping cost or future demand.
    - Negative transaction lines are not guaranteed to be returns.
    - Customer IDs may be missing, so customer metrics cover identified customers only.
    - The final dataset month is partial.
    - Historical sales do not prove that a market or product will perform similarly in the future.
    """)

st.divider()
st.markdown('<div class="footer">MAISON & MERCANTILE · COMMERCIAL INTELLIGENCE · POWERED BY DUCKDB & LOCAL AI</div>',unsafe_allow_html=True)
