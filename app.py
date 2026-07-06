"""
E-Commerce Sales Analytics Dashboard
=====================================
A premium, BI-grade analytics dashboard built with Flask, Pandas and Plotly.

Author: Data Science Major Project
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import plotly.utils
import os

app = Flask(__name__)

# ----------------------------------------------------------------------------
# GLOBAL THEME CONFIG FOR PLOTLY (dark, premium BI look)
# ----------------------------------------------------------------------------
PLOTLY_TEMPLATE = "plotly_dark"

COLORWAY = [
    "#6366F1", "#22D3EE", "#F472B6", "#34D399", "#FBBF24",
    "#A78BFA", "#FB923C", "#60A5FA", "#F87171", "#4ADE80",
]

CHART_BG = "rgba(0,0,0,0)"
PAPER_BG = "rgba(0,0,0,0)"
FONT_COLOR = "#CBD5E1"
GRID_COLOR = "rgba(148,163,184,0.12)"


def base_layout(fig, title=None, height=380, legend=True):
    """Apply a consistent premium dark styling to every Plotly figure."""
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family="Inter, Segoe UI, sans-serif", color=FONT_COLOR, size=12),
        title=dict(text=title, font=dict(size=15, color="#E2E8F0", family="Inter, sans-serif"),
                    x=0.02, xanchor="left") if title else None,
        margin=dict(l=40, r=20, t=50 if title else 20, b=40),
        height=height,
        colorway=COLORWAY,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11),
        ) if legend else dict(visible=False),
        hoverlabel=dict(bgcolor="#1E293B", font_size=12, font_family="Inter, sans-serif",
                         bordercolor="#334155"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID_COLOR, tickfont=dict(color="#94A3B8"))
    fig.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, zeroline=False, tickfont=dict(color="#94A3B8"))
    return fig


def to_json(fig):
    """
    Convert a Plotly Figure into a plain JSON-serializable Python dict
    (NOT a pre-stringified JSON string).

    IMPORTANT: We intentionally return a dict/list structure here instead of
    a raw JSON string. The templates embed this value into an HTML attribute
    using Jinja's built-in `|tojson` filter, which safely escapes quotes,
    angle brackets and ampersands for HTML-attribute context. If we returned
    a plain string and dropped it in with `|safe` instead, any single-quote
    character inside the figure (e.g. the font-family "'Segoe UI'", or a
    real data value like the city name "Santa Barbara D'Oeste") would
    prematurely close the single-quoted HTML attribute, corrupt the DOM for
    that chart, and cascade into every chart rendered after it on the page.
    """
    return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))


# ----------------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------------
DATA_PATH = os.path.join(os.path.dirname(__file__), "cleaned_ecommerce.csv")

def load_data():
    df = pd.read_csv(DATA_PATH)

    # Parse dates
    date_cols = [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date", "shipping_limit_date",
    ]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # Clean text fields
    for c in ["customer_city", "seller_city"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.title()

    # Fill category names
    df["product_category_name_english"] = df["product_category_name_english"].fillna("unknown").replace("nan", "unknown")
    df["product_category_name_english"] = df["product_category_name_english"].str.replace("_", " ").str.title()

    df["payment_type"] = df["payment_type"].fillna("unknown")
    df["payment_type_label"] = df["payment_type"].str.replace("_", " ").str.title()

    # Month ordering
    month_order = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df["Weekday"] = pd.Categorical(df["Weekday"], categories=weekday_order, ordered=True)

    df["YearMonth"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)

    return df


RAW_DF = load_data()


def apply_filters(df, args):
    """Apply query-string filters (year, month, state, payment_type, category)."""
    year = args.get("year", "all")
    month = args.get("month", "all")
    state = args.get("state", "all")
    payment = args.get("payment_type", "all")
    category = args.get("category", "all")

    if year and year != "all":
        df = df[df["Year"] == int(year)]
    if month and month != "all":
        df = df[df["Month"] == month]
    if state and state != "all":
        df = df[df["customer_state"] == state]
    if payment and payment != "all":
        df = df[df["payment_type"] == payment]
    if category and category != "all":
        df = df[df["product_category_name_english"] == category]

    return df


def filter_options(df):
    return {
        "years": sorted(df["Year"].dropna().unique().tolist()),
        "months": [m for m in df["Month"].cat.categories if m in df["Month"].unique()],
        "states": sorted(df["customer_state"].dropna().unique().tolist()),
        "payment_types": sorted([p for p in df["payment_type"].dropna().unique().tolist() if p != "unknown"]),
        "categories": sorted(df["product_category_name_english"].dropna().unique().tolist()),
    }


# ----------------------------------------------------------------------------
# KPI CALCULATIONS
# ----------------------------------------------------------------------------
def compute_kpis(df):
    total_sales = float(df["price"].sum())
    total_revenue = float(df["Total_Amount"].sum()) if "Total_Amount" in df.columns else float(df["payment_value"].sum())
    total_orders = int(df["order_id"].nunique())
    total_customers = int(df["customer_unique_id"].nunique())
    total_products = int(df["product_id"].nunique())
    total_sellers = int(df["seller_id"].nunique())
    avg_rating = float(df["review_score"].mean()) if df["review_score"].notna().any() else 0.0
    avg_delivery = float(df["Delivery_Days"].mean()) if df["Delivery_Days"].notna().any() else 0.0
    avg_order_value = float(df.groupby("order_id")["Total_Amount"].sum().mean()) if total_orders else 0.0

    return {
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_products": total_products,
        "total_sellers": total_sellers,
        "avg_rating": round(avg_rating, 2),
        "avg_delivery": round(avg_delivery, 1),
        "avg_order_value": round(avg_order_value, 2),
    }


def fmt_currency(value):
    """Human friendly currency formatting e.g. 1.2M / 345.6K"""
    if value is None:
        return "R$ 0"
    abs_v = abs(value)
    if abs_v >= 1_000_000:
        return f"R$ {value/1_000_000:.2f}M"
    if abs_v >= 1_000:
        return f"R$ {value/1_000:.1f}K"
    return f"R$ {value:.2f}"


app.jinja_env.filters["currency"] = fmt_currency
app.jinja_env.filters["intcomma"] = lambda v: f"{int(v):,}"


# ----------------------------------------------------------------------------
# CHART BUILDERS
# ----------------------------------------------------------------------------
def chart_monthly_sales_trend(df):
    g = df.groupby("YearMonth").agg(sales=("price", "sum")).reset_index().sort_values("YearMonth")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=g["YearMonth"], y=g["sales"], mode="lines", name="Sales",
        line=dict(color="#6366F1", width=3, shape="spline"),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.15)",
        hovertemplate="%{x}<br>Sales: R$ %{y:,.2f}<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    return to_json(fig)


def chart_monthly_orders(df):
    g = df.groupby("YearMonth").agg(orders=("order_id", "nunique")).reset_index().sort_values("YearMonth")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["YearMonth"], y=g["orders"], name="Orders",
        marker=dict(color="#22D3EE", line=dict(width=0)),
        hovertemplate="%{x}<br>Orders: %{y:,}<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    fig.update_traces(marker_cornerradius=6)
    return to_json(fig)


def chart_revenue_by_month(df):
    g = df.groupby("Month", observed=True).agg(revenue=("Total_Amount", "sum")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["Month"].astype(str), y=g["revenue"], name="Revenue",
        marker=dict(color=g["revenue"], colorscale=[[0, "#312E81"], [1, "#818CF8"]], showscale=False),
        hovertemplate="%{x}<br>Revenue: R$ %{y:,.2f}<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    fig.update_traces(marker_cornerradius=6)
    return to_json(fig)


def chart_payment_pie(df):
    g = df.drop_duplicates("order_id").groupby("payment_type_label").size().reset_index(name="count")
    g = g.sort_values("count", ascending=False)
    fig = go.Figure(data=[go.Pie(
        labels=g["payment_type_label"], values=g["count"], hole=0.62,
        marker=dict(colors=COLORWAY, line=dict(color="#0B1120", width=2)),
        textinfo="percent", textfont=dict(size=12, color="#E2E8F0"),
        hovertemplate="%{label}<br>%{value:,} orders (%{percent})<extra></extra>",
    )])
    base_layout(fig, height=340)
    fig.update_layout(showlegend=True)
    return to_json(fig)


def chart_top_categories(df, n=10):
    g = df.groupby("product_category_name_english").agg(sales=("price", "sum")).reset_index()
    g = g.sort_values("sales", ascending=False).head(n).sort_values("sales")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["sales"], y=g["product_category_name_english"], orientation="h",
        marker=dict(color=g["sales"], colorscale=[[0, "#164E63"], [1, "#22D3EE"]], showscale=False),
        hovertemplate="%{y}<br>Sales: R$ %{x:,.2f}<extra></extra>",
    ))
    base_layout(fig, height=420, legend=False)
    fig.update_traces(marker_cornerradius=4)
    fig.update_yaxes(tickfont=dict(size=11))
    return to_json(fig)


def chart_top_states(df, n=10):
    g = df.drop_duplicates("order_id").groupby("customer_state").size().reset_index(name="orders")
    g = g.sort_values("orders", ascending=False).head(n).sort_values("orders")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["orders"], y=g["customer_state"], orientation="h",
        marker=dict(color=g["orders"], colorscale=[[0, "#4C1D95"], [1, "#A78BFA"]], showscale=False),
        hovertemplate="%{y}<br>Orders: %{x:,}<extra></extra>",
    ))
    base_layout(fig, height=420, legend=False)
    fig.update_traces(marker_cornerradius=4)
    return to_json(fig)


def chart_top_sellers(df, n=10):
    g = df.groupby("seller_id").agg(revenue=("Total_Amount", "sum")).reset_index()
    g = g.sort_values("revenue", ascending=False).head(n)
    g["seller_short"] = g["seller_id"].str[:8] + "…"
    g = g.sort_values("revenue")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["revenue"], y=g["seller_short"], orientation="h",
        marker=dict(color=g["revenue"], colorscale=[[0, "#7C2D12"], [1, "#FB923C"]], showscale=False),
        hovertemplate="Seller %{y}<br>Revenue: R$ %{x:,.2f}<extra></extra>",
    ))
    base_layout(fig, height=420, legend=False)
    fig.update_traces(marker_cornerradius=4)
    return to_json(fig)


def chart_review_distribution(df):
    g = df.dropna(subset=["review_score"]).groupby("review_score").size().reset_index(name="count")
    g = g.sort_values("review_score")
    colors = ["#F87171", "#FB923C", "#FBBF24", "#A3E635", "#34D399"]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["review_score"].astype(int).astype(str), y=g["count"],
        marker=dict(color=colors[:len(g)]),
        hovertemplate="Rating %{x} ⭐<br>%{y:,} reviews<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    fig.update_traces(marker_cornerradius=6)
    fig.update_xaxes(title="Rating")
    return to_json(fig)


def chart_delivery_days(df):
    d = df["Delivery_Days"].dropna()
    d = d[(d >= 0) & (d <= 60)]
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=d, nbinsx=30, marker=dict(color="#34D399"),
        hovertemplate="%{x} days<br>%{y:,} orders<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    fig.update_xaxes(title="Delivery Days")
    fig.update_traces(marker_cornerradius=3)
    return to_json(fig)


def chart_avg_order_value(df):
    # Two-step groupby/mean instead of a nested .groupby().apply(): the
    # nested-apply form returns a Series when there's at least one group,
    # but pandas silently returns an empty DataFrame (not a Series) when
    # the input group is empty (e.g. a filter combination with zero
    # matching rows) — and DataFrame.reset_index() doesn't accept the
    # `name=` kwarg that Series.reset_index() does, which crashed the
    # whole page with a 500 error for that filter combination. Building
    # the aggregation as two plain groupby/mean calls avoids the
    # apply()-return-type ambiguity and behaves correctly (empty result)
    # for empty input.
    order_totals = (
        df.groupby(["YearMonth", "order_id"])["Total_Amount"]
        .sum()
        .reset_index()
    )
    g = (
        order_totals.groupby("YearMonth")["Total_Amount"]
        .mean()
        .reset_index(name="aov")
        .sort_values("YearMonth")
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=g["YearMonth"], y=g["aov"], mode="lines+markers", name="AOV",
        line=dict(color="#F472B6", width=3), marker=dict(size=6, color="#F472B6"),
        hovertemplate="%{x}<br>AOV: R$ %{y:,.2f}<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    return to_json(fig)


def chart_orders_weekday(df):
    g = df.drop_duplicates("order_id").groupby("Weekday", observed=True).size().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ).reset_index(name="orders")
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=g["orders"], theta=g["Weekday"], fill="toself",
        line=dict(color="#60A5FA"), fillcolor="rgba(96,165,250,0.25)",
        hovertemplate="%{theta}<br>%{r:,} orders<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=CHART_BG,
            radialaxis=dict(showticklabels=True, gridcolor=GRID_COLOR, color="#94A3B8"),
            angularaxis=dict(gridcolor=GRID_COLOR, color="#CBD5E1"),
        ),
    )
    base_layout(fig, height=360, legend=False)
    return to_json(fig)


def chart_customer_state_distribution(df):
    g = df.drop_duplicates("customer_unique_id").groupby("customer_state").size().reset_index(name="customers")
    g = g.sort_values("customers", ascending=False).head(15)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["customer_state"], y=g["customers"],
        marker=dict(color=g["customers"], colorscale=[[0, "#1E3A8A"], [1, "#60A5FA"]], showscale=False),
        hovertemplate="%{x}<br>%{y:,} customers<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    fig.update_traces(marker_cornerradius=6)
    return to_json(fig)


# ---- product page ----
def chart_top_products(df, n=10):
    g = df.groupby("product_id").agg(revenue=("Total_Amount", "sum"), qty=("order_id", "count")).reset_index()
    g = g.sort_values("revenue", ascending=False).head(n)
    g["product_short"] = g["product_id"].str[:8] + "…"
    g = g.sort_values("revenue")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["revenue"], y=g["product_short"], orientation="h",
        marker=dict(color=g["revenue"], colorscale=[[0, "#134E4A"], [1, "#2DD4BF"]], showscale=False),
        hovertemplate="Product %{y}<br>Revenue: R$ %{x:,.2f}<extra></extra>",
    ))
    base_layout(fig, height=420, legend=False)
    fig.update_traces(marker_cornerradius=4)
    return to_json(fig)


def category_table(df, n=15):
    g = df.groupby("product_category_name_english").agg(
        products=("product_id", "nunique"),
        orders=("order_id", "nunique"),
        sales=("price", "sum"),
        avg_price=("price", "mean"),
        avg_rating=("review_score", "mean"),
    ).reset_index().sort_values("sales", ascending=False).head(n)
    g["sales"] = g["sales"].round(2)
    g["avg_price"] = g["avg_price"].round(2)
    g["avg_rating"] = g["avg_rating"].round(2)
    return g.to_dict(orient="records")


# ---- customer page ----
def chart_customer_city(df, n=10):
    g = df.drop_duplicates("customer_unique_id").groupby("customer_city").size().reset_index(name="customers")
    g = g.sort_values("customers", ascending=False).head(n).sort_values("customers")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["customers"], y=g["customer_city"], orientation="h",
        marker=dict(color=g["customers"], colorscale=[[0, "#581C87"], [1, "#D8B4FE"]], showscale=False),
        hovertemplate="%{y}<br>%{x:,} customers<extra></extra>",
    ))
    base_layout(fig, height=420, legend=False)
    fig.update_traces(marker_cornerradius=4)
    return to_json(fig)


def top_customers_table(df, n=15):
    g = df.groupby("customer_unique_id").agg(
        orders=("order_id", "nunique"),
        spent=("Total_Amount", "sum"),
        city=("customer_city", "first"),
        state=("customer_state", "first"),
    ).reset_index().sort_values("spent", ascending=False).head(n)
    g["spent"] = g["spent"].round(2)
    g["customer_unique_id"] = g["customer_unique_id"].str[:10] + "…"
    return g.to_dict(orient="records")


# ---- payments page ----
def chart_installments(df):
    g = df.dropna(subset=["payment_installments"]).copy()
    g["payment_installments"] = g["payment_installments"].astype(int)
    g = g[g["payment_installments"] <= 18]
    g = g.groupby("payment_installments").size().reset_index(name="count")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["payment_installments"], y=g["count"],
        marker=dict(color="#FBBF24"),
        hovertemplate="%{x} installments<br>%{y:,} payments<extra></extra>",
    ))
    base_layout(fig, height=360, legend=False)
    fig.update_xaxes(title="Installments", dtick=1)
    fig.update_traces(marker_cornerradius=6)
    return to_json(fig)


def chart_payment_revenue(df):
    g = df.groupby("payment_type_label").agg(revenue=("payment_value", "sum")).reset_index()
    g = g.sort_values("revenue", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["payment_type_label"], y=g["revenue"],
        marker=dict(color=COLORWAY),
        hovertemplate="%{x}<br>Revenue: R$ %{y:,.2f}<extra></extra>",
    ))
    base_layout(fig, height=360, legend=False)
    fig.update_traces(marker_cornerradius=6)
    return to_json(fig)


def chart_payment_trend(df):
    g = df.groupby(["YearMonth", "payment_type_label"]).size().reset_index(name="count")
    fig = px.line(g, x="YearMonth", y="count", color="payment_type_label")
    fig.update_traces(mode="lines+markers", line=dict(width=2.5), marker=dict(size=5))
    base_layout(fig, height=360)
    return to_json(fig)


# ---- reviews page ----
def chart_review_by_category(df, n=10):
    g = df.dropna(subset=["review_score"]).groupby("product_category_name_english").agg(
        avg_rating=("review_score", "mean"), reviews=("review_score", "count")
    ).reset_index()
    g = g[g["reviews"] >= 20].sort_values("avg_rating", ascending=False).head(n).sort_values("avg_rating")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["avg_rating"], y=g["product_category_name_english"], orientation="h",
        marker=dict(color=g["avg_rating"], colorscale=[[0, "#F87171"], [1, "#34D399"]], showscale=False),
        hovertemplate="%{y}<br>Avg Rating: %{x:.2f}<extra></extra>",
    ))
    base_layout(fig, height=420, legend=False)
    fig.update_traces(marker_cornerradius=4)
    fig.update_xaxes(range=[0, 5])
    return to_json(fig)


def chart_review_trend(df):
    g = df.dropna(subset=["review_score"]).groupby("YearMonth").agg(avg_rating=("review_score", "mean")).reset_index().sort_values("YearMonth")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=g["YearMonth"], y=g["avg_rating"], mode="lines+markers",
        line=dict(color="#FBBF24", width=3), marker=dict(size=6),
        hovertemplate="%{x}<br>Avg Rating: %{y:.2f}<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    fig.update_yaxes(range=[0, 5])
    return to_json(fig)


# ---- sellers page ----
def chart_seller_states(df, n=12):
    g = df.drop_duplicates("seller_id").groupby("seller_state").size().reset_index(name="sellers")
    g = g.sort_values("sellers", ascending=False).head(n)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["seller_state"], y=g["sellers"],
        marker=dict(color=g["sellers"], colorscale=[[0, "#7C2D12"], [1, "#FDBA74"]], showscale=False),
        hovertemplate="%{x}<br>%{y:,} sellers<extra></extra>",
    ))
    base_layout(fig, height=340, legend=False)
    fig.update_traces(marker_cornerradius=6)
    return to_json(fig)


def seller_table(df, n=15):
    g = df.groupby("seller_id").agg(
        revenue=("Total_Amount", "sum"),
        orders=("order_id", "nunique"),
        avg_rating=("review_score", "mean"),
        state=("seller_state", "first"),
        city=("seller_city", "first"),
    ).reset_index().sort_values("revenue", ascending=False).head(n)
    g["revenue"] = g["revenue"].round(2)
    g["avg_rating"] = g["avg_rating"].round(2)
    g["seller_id"] = g["seller_id"].str[:10] + "…"
    return g.to_dict(orient="records")


# ----------------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------------
@app.route("/")
def dashboard():
    df = apply_filters(RAW_DF, request.args)
    kpis = compute_kpis(df)
    charts = {
        "monthly_sales_trend": chart_monthly_sales_trend(df),
        "monthly_orders": chart_monthly_orders(df),
        "revenue_by_month": chart_revenue_by_month(df),
        "payment_pie": chart_payment_pie(df),
        "top_categories": chart_top_categories(df),
        "top_states": chart_top_states(df),
        "top_sellers": chart_top_sellers(df),
        "review_distribution": chart_review_distribution(df),
        "delivery_days": chart_delivery_days(df),
        "avg_order_value": chart_avg_order_value(df),
        "orders_weekday": chart_orders_weekday(df),
        "customer_state_distribution": chart_customer_state_distribution(df),
    }
    return render_template(
        "dashboard.html",
        active="dashboard",
        kpis=kpis,
        charts=charts,
        filters=filter_options(RAW_DF),
        current_filters=request.args,
    )


@app.route("/products")
def products():
    df = apply_filters(RAW_DF, request.args)
    kpis = compute_kpis(df)
    charts = {
        "top_categories": chart_top_categories(df, 10),
        "top_products": chart_top_products(df, 10),
    }
    table = category_table(df)
    return render_template(
        "products.html",
        active="products",
        kpis=kpis,
        charts=charts,
        table=table,
        filters=filter_options(RAW_DF),
        current_filters=request.args,
    )


@app.route("/customers")
def customers():
    df = apply_filters(RAW_DF, request.args)
    kpis = compute_kpis(df)
    charts = {
        "customer_state_distribution": chart_customer_state_distribution(df),
        "customer_city": chart_customer_city(df, 10),
    }
    table = top_customers_table(df)
    return render_template(
        "customers.html",
        active="customers",
        kpis=kpis,
        charts=charts,
        table=table,
        filters=filter_options(RAW_DF),
        current_filters=request.args,
    )


@app.route("/payments")
def payments():
    df = apply_filters(RAW_DF, request.args)
    kpis = compute_kpis(df)
    charts = {
        "payment_pie": chart_payment_pie(df),
        "installments": chart_installments(df),
        "payment_revenue": chart_payment_revenue(df),
        "payment_trend": chart_payment_trend(df),
    }
    return render_template(
        "payments.html",
        active="payments",
        kpis=kpis,
        charts=charts,
        filters=filter_options(RAW_DF),
        current_filters=request.args,
    )


@app.route("/reviews")
def reviews():
    df = apply_filters(RAW_DF, request.args)
    kpis = compute_kpis(df)
    charts = {
        "review_distribution": chart_review_distribution(df),
        "review_by_category": chart_review_by_category(df),
        "review_trend": chart_review_trend(df),
    }
    return render_template(
        "reviews.html",
        active="reviews",
        kpis=kpis,
        charts=charts,
        filters=filter_options(RAW_DF),
        current_filters=request.args,
    )


@app.route("/sellers")
def sellers():
    df = apply_filters(RAW_DF, request.args)
    kpis = compute_kpis(df)
    charts = {
        "top_sellers": chart_top_sellers(df, 10),
        "seller_states": chart_seller_states(df),
    }
    table = seller_table(df)
    return render_template(
        "sellers.html",
        active="sellers",
        kpis=kpis,
        charts=charts,
        table=table,
        filters=filter_options(RAW_DF),
        current_filters=request.args,
    )


@app.route("/about")
def about():
    kpis = compute_kpis(RAW_DF)
    return render_template("about.html", active="about", kpis=kpis, filters=filter_options(RAW_DF), current_filters=request.args)


@app.route("/api/kpis")
def api_kpis():
    df = apply_filters(RAW_DF, request.args)
    return jsonify(compute_kpis(df))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
