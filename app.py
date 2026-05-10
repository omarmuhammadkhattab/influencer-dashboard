"""
app.py — Influencer Analytics Dashboard
Reads live data from Shopify Admin API and renders an interactive dashboard.
"""

import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

STORE   = os.getenv("SHOPIFY_STORE")
TOKEN   = os.getenv("SHOPIFY_TOKEN")
BASE    = f"https://{STORE}/admin/api/2024-01"
HEADERS = {"X-Shopify-Access-Token": TOKEN}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Influencer Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .tier-A { color: #2ecc71; font-weight: bold; }
    .tier-B { color: #f39c12; font-weight: bold; }
    .tier-C { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Data fetching ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_orders():
    """Fetch all orders from Shopify Admin API with pagination."""
    orders = []
    url = f"{BASE}/orders.json?status=any&limit=250"
    while url:
        resp = requests.get(url, headers=HEADERS)
        data = resp.json()
        orders.extend(data.get("orders", []))
        # Handle pagination via Link header
        link = resp.headers.get("Link", "")
        url  = None
        if 'rel="next"' in link:
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip().strip("<>")
    return orders

def parse_orders(raw_orders):
    """Parse raw Shopify orders into a clean DataFrame."""
    rows = []
    for o in raw_orders:
        tags = [t.strip().lower() for t in o.get("tags", "").split(",")]
        code = o["discount_codes"][0]["code"] if o.get("discount_codes") else None
        rows.append({
            "order_id":      o["id"],
            "created_at":    pd.to_datetime(o["created_at"]),
            "total_price":   float(o.get("total_price", 0)),
            "discount_code": code,
            "channel":       "meta_ad" if "meta_ad" in tags else ("organic" if "organic" in tags else "influencer"),
            "returned":      "retourniert" in tags,
            "partial_return":"teilretourniert" in tags,
        })
    return pd.DataFrame(rows)

def compute_metrics(df):
    """Compute per-influencer metrics."""
    inf_df = df[df["discount_code"].notna()].copy()

    metrics = []
    for code, group in inf_df.groupby("discount_code"):
        total_orders  = len(group)
        total_revenue = group["total_price"].sum()
        returned      = group["returned"].sum() + group["partial_return"].sum()
        return_rate   = returned / total_orders if total_orders > 0 else 0

        # Separate influencer-driven vs Meta Ad traffic using same code
        influencer_orders = len(group[group["channel"] == "influencer"])
        meta_orders       = len(group[group["channel"] == "meta_ad"])

        net_revenue = total_revenue * (1 - return_rate)
        metrics.append({
            "Influencer":         code,
            "Total Orders":       total_orders,
            "Influencer Orders":  influencer_orders,
            "Meta Ad Orders":     meta_orders,
            "Gross Revenue (€)":  round(total_revenue, 2),
            "Return Rate (%)":    round(return_rate * 100, 1),
            "Net Revenue (€)":    round(net_revenue, 2),
        })

    mdf = pd.DataFrame(metrics).sort_values("Net Revenue (€)", ascending=False)

    # Worth It Score: percentile rank of net revenue (0–100)
    mdf["Worth It Score"] = (
        mdf["Net Revenue (€)"].rank(pct=True) * 100
    ).round(1)

    # Tier assignment based on score
    mdf["Tier"] = pd.cut(
        mdf["Worth It Score"],
        bins=[0, 33, 66, 100],
        labels=["C", "B", "A"],
        include_lowest=True
    )
    return mdf

# ── Main app ──────────────────────────────────────────────────────────────────
st.title("📊 Influencer Analytics Dashboard")
st.caption("Live data from Shopify · influencer-analytics-demo")

with st.spinner("Fetching orders from Shopify..."):
    raw   = fetch_orders()
    df    = parse_orders(raw)
    mdf   = compute_metrics(df)

# ── Filters ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filters")
    date_range = st.date_input(
        "Date range",
        value=(df["created_at"].min().date(), df["created_at"].max().date())
    )
    selected_tiers = st.multiselect(
        "Tier filter",
        options=["A", "B", "C"],
        default=["A", "B", "C"]
    )
    st.markdown("---")
    st.caption("Tier A = top performers\nTier B = borderline\nTier C = not worth it")

# Apply date filter
df_f = df[
    (df["created_at"].dt.date >= date_range[0]) &
    (df["created_at"].dt.date <= date_range[1])
]
mdf_f = compute_metrics(df_f)
mdf_f = mdf_f[mdf_f["Tier"].isin(selected_tiers)]

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Orders",       f"{len(df_f):,}")
k2.metric("Gross Revenue",      f"€{df_f['total_price'].sum():,.0f}")
k3.metric("Avg Return Rate",    f"{(df_f['returned'].sum() / len(df_f) * 100):.1f}%")
k4.metric("Top Influencer",     mdf_f.iloc[0]["Influencer"] if len(mdf_f) else "—")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Revenue", "↩️ Returns", "🎯 Worth It?"])

with tab1:
    st.subheader("Gross Revenue per Influencer")
    fig1 = px.bar(
        mdf_f.sort_values("Gross Revenue (€)"),
        x="Gross Revenue (€)", y="Influencer",
        orientation="h",
        color="Tier",
        color_discrete_map={"A": "#2ecc71", "B": "#f39c12", "C": "#e74c3c"},
        text="Gross Revenue (€)"
    )
    fig1.update_traces(texttemplate="€%{text:,.0f}", textposition="outside")
    fig1.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Return Rate per Influencer")
    fig2 = px.bar(
        mdf_f.sort_values("Return Rate (%)", ascending=False),
        x="Return Rate (%)", y="Influencer",
        orientation="h",
        color="Return Rate (%)",
        color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
        text="Return Rate (%)"
    )
    fig2.update_traces(texttemplate="%{text}%", textposition="outside")
    fig2.update_layout(height=600)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Revenue vs Return Rate — The 'Worth It' Quadrant")
    st.caption("✅ Bottom-right = high revenue, low returns = best collaborations")

    fig3 = px.scatter(
        mdf_f,
        x="Return Rate (%)",
        y="Net Revenue (€)",
        size="Total Orders",
        color="Tier",
        color_discrete_map={"A": "#2ecc71", "B": "#f39c12", "C": "#e74c3c"},
        text="Influencer",
        hover_data=["Total Orders", "Gross Revenue (€)", "Worth It Score"]
    )
    fig3.update_traces(textposition="top center")

    # Add quadrant lines
    mid_x = mdf_f["Return Rate (%)"].median()
    mid_y = mdf_f["Net Revenue (€)"].median()
    fig3.add_hline(y=mid_y, line_dash="dash", line_color="gray", opacity=0.4)
    fig3.add_vline(x=mid_x, line_dash="dash", line_color="gray", opacity=0.4)
    fig3.update_layout(height=500)
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Full Ranking Table")
    st.dataframe(
        mdf_f[[
            "Influencer", "Tier", "Worth It Score",
            "Total Orders", "Influencer Orders", "Meta Ad Orders",
            "Gross Revenue (€)", "Return Rate (%)", "Net Revenue (€)"
        ]].sort_values("Worth It Score", ascending=False).reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

# ── Attribution note ──────────────────────────────────────────────────────────
with st.expander("ℹ️ About Meta Ads Attribution"):
    st.markdown("""
    Some orders use an influencer discount code but were driven by **Meta Ads**, not the influencer directly.
    These are identified via the order tag `meta_ad` (set during seeding to simulate UTM-based attribution).

    In production, this would be handled by reading **UTM parameters** from Shopify's order source URL,
    allowing precise separation of organic influencer traffic from paid ad traffic using the same code.
    """)
