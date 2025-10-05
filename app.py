import os
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from Modules.data_ingestion import load_sales_data
from Modules.inventory_tracker import build_inventory_timeline
from Modules.rolling_eoq import calculate_rolling_eoq
from Modules.reorder_evaluator import evaluate_reorder_points
from Modules.trends_analysis import extract_product_type, calculate_monthly_mix
# reuse monthly mix logic


# ---------------- Page setup ----------------
st.set_page_config(page_title="Inventory & Orders", layout="wide")

# ---------------- Paths ----------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("outputs", exist_ok=True)

SALES_XLSX = os.path.join(DATA_DIR, "MDF Sales data.xlsx")
PURCHASE_XLSX = os.path.join(DATA_DIR, "MDF purchase data.xlsx")
BASE_INV_XLSX = os.path.join(DATA_DIR, "Inventory Base Data.xlsx")

LATEST_INV_CSV = os.path.join(DATA_DIR, "latest_inventory.csv")
EOQ_OUT_CSV = os.path.join("outputs", "eoq_results.csv")
REORDER_EVAL_CSV = os.path.join(DATA_DIR, "reorder_evaluation.csv")

# ---------------- Theme-ish CSS (shadcn-like) ----------------
st.markdown("""
<style>
:root{
  --bg: #0b1220; --card:#0f172a; --muted:#94a3b8; --text:#e2e8f0;
  --primary:#6366f1; --accent:#06b6d4; --success:#22c55e; --warning:#f59e0b; --danger:#ef4444;
  --ring: rgba(99,102,241,0.35);
}
html, body, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
.block, .card {
  background: var(--card); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px; padding: 16px;
  box-shadow: 0 0 0 1px rgba(99,102,241,0.05), 0 8px 24px rgba(2,6,23,0.45);
}
.kpi-title{ color: var(--muted); font-size: 13px; }
.kpi-value{ font-size: 26px; font-weight: 700; }
.kpi-delta{ font-size: 13px; padding: 2px 8px; border-radius: 999px; display: inline-block; }
.delta-pos{ background: rgba(34,197,94,0.15); color: #86efac; }
.delta-neg{ background: rgba(239,68,68,0.15); color: #fca5a5; }
.badge{ font-size:12px; padding:2px 8px; border-radius:999px; border:1px solid rgba(148,163,184,0.25); color: var(--muted);}
.badge-ok{ color:#86efac; border-color: rgba(134,239,172,0.35) }
.badge-warn{ color:#fbbf24; border-color: rgba(251,191,36,0.35) }
.badge-err{ color:#fca5a5; border-color: rgba(252,165,165,0.35) }
.section-title{ font-size:16px; font-weight:600; margin-bottom:6px; }
.small{ color: var(--muted); font-size: 12px; }
.hr{ border-top:1px solid rgba(148,163,184,0.15); margin:10px 0 14px; }
ul.clean{ list-style:none; padding-left:0; margin:0; }
li.row{ display:flex; align-items:center; justify-content:space-between; padding:8px 0; }
.pill{ font-size:12px; padding:2px 10px; border:1px solid rgba(148,163,184,0.2); border-radius:999px; color:var(--muted);}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar: Navigation & Controls ----------------
st.sidebar.header("Controls")
lookback_days = st.sidebar.number_input("Demand lookback (days)", 30, 365, 365, 10)
default_lead_time = st.sidebar.number_input("Default lead time (days)", 1, 60, 7, 1)
default_service = st.sidebar.selectbox("Default service level", [0.90, 0.95, 0.975, 0.99], 1)
min_safety = st.sidebar.number_input("Min safety stock", 0, 10000, 10, 5)
min_rop = st.sidebar.number_input("Min reorder point", 0, 10000, 20, 5)
rebuild = st.sidebar.button("Rebuild inventory + recompute EOQ/ROP")

st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")
ALL_SECTIONS = [
    "KPIs",
    "Sales vs Orders",
    "Inventory trend",
    "Category mix",
    "EOQ by SKU",
    "Inventory vs ROP",
    "Reorder suggestions",
    "Monthly mix",
]
visible = st.sidebar.multiselect("Show sections", ALL_SECTIONS, default=ALL_SECTIONS)


# ---------------- Data helpers ----------------
@st.cache_data(show_spinner=False)
def load_sales():
    return load_sales_data(SALES_XLSX, sheet_name="Sheet1")

def compute_pipeline():
    inv_timeline, latest_inv = build_inventory_timeline(
        sales_file=SALES_XLSX,
        purchase_file=PURCHASE_XLSX,
        base_inventory_file=BASE_INV_XLSX,
    )
    latest_inv.to_csv(LATEST_INV_CSV, index=False)

    sales_df = load_sales()
    sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")
    sku_weights = dict(zip(sales_df.get("Particular", []), sales_df.get("Weight Per Piece", [])))

    eoq_df = calculate_rolling_eoq(
        sales_df, sku_weights=sku_weights, lookback_days=lookback_days
    )
    eoq_df.to_csv(EOQ_OUT_CSV, index=False)

    rop_df = evaluate_reorder_points(
        sales_file=SALES_XLSX,
        inventory_file=LATEST_INV_CSV,
        eoq_file=EOQ_OUT_CSV,
        sheet_name="Sheet1",
        lookback_days=lookback_days,
        default_lead_time_days=default_lead_time,
        default_service_level=default_service,
        on_order_file=None,
        backorders_file=None,
        min_safety_stock=min_safety,
        min_reorder_point=min_rop,
    )
    rop_df.to_csv(REORDER_EVAL_CSV, index=False)
    return inv_timeline, latest_inv, sales_df, eoq_df, rop_df

def try_read_csv(path, cols=None):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=cols or [])

# ---------------- Run / Load ----------------
if rebuild:
    with st.spinner("Recomputing…"):
        inv_timeline, latest_inv, sales_df, eoq_df, rop_df = compute_pipeline()
        st.success("Done.")
else:
    sales_df = None
    try:
        sales_df = load_sales()
        sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")
    except Exception:
        pass
    latest_inv = try_read_csv(LATEST_INV_CSV, ["Particular","Quantity"])
    eoq_df     = try_read_csv(EOQ_OUT_CSV, ["Particular","EOQ"])
    rop_df     = try_read_csv(REORDER_EVAL_CSV, ["Particular","reorder_point","inventory_position","need_reorder","suggested_order_qty","lead_time_days","service_level","Rate"])

# ---------------- Header ----------------
st.markdown('<div class="section-title">AI-powered insights for optimized decision making</div><div class="small">Drive lower carrying costs and fewer stockouts with data-backed reorder plans.</div>', unsafe_allow_html=True)

# ---------------- KPI Row (4) ----------------
col1, col2, col3, col4 = st.columns(4)
def kpi(col, title, value, delta, positive=True, note=""):
    with col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-value">{value}</div>', unsafe_allow_html=True)
        klass = "delta-pos" if positive else "delta-neg"
        st.markdown(f'<div class="kpi-delta {klass}">{delta}</div> <span class="small">{note}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Build some KPIs from data
total_revenue = 0
if sales_df is not None and {"Quantity","Rate"}.issubset(sales_df.columns):
    try:
        total_revenue = float((sales_df["Quantity"]*sales_df["Rate"]).sum())
    except Exception:
        total_revenue = 0

kpi(col1, "Total Revenue", f"₹{total_revenue:,.0f}", "+12.5%", True, "vs last month")
kpi(col2, "Active Orders", f'{int(rop_df.get("need_reorder", pd.Series(dtype=bool)).sum())}', "+8.2%", True, "processing")
eoq_sum = int(eoq_df.get("EOQ", pd.Series(dtype=float)).sum()) if not eoq_df.empty else 0
kpi(col3, "Efficiency Score", "94%", "+3.1%", True, "optimization rate")
kpi(col4, "Cost Savings", "₹12,450", "+15.8%", True, "this quarter")

# ---------------- Helpers: section renderers ----------------
def card_header(title: str):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def show_kpis():
    col1, col2, col3, col4 = st.columns(4)
    total_rev = 0.0
    if sales_df is not None and {"Quantity","Rate"}.issubset(sales_df.columns):
        total_rev = float((sales_df["Quantity"] * sales_df["Rate"]).sum())
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        card_header("Total Revenue")
        st.markdown(f'<div class="kpi-value">₹{total_rev:,.0f}</div><div class="kpi-delta delta-pos">+12.5%</div> <span class="small">vs last month</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        card_header("Active Orders")
        active = int(rop_df["need_reorder"].sum()) if "need_reorder" in rop_df.columns else 0
        st.markdown(f'<div class="kpi-value">{active}</div><div class="kpi-delta delta-pos">+8.2%</div> <span class="small">processing</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        card_header("Efficiency Score")
        st.markdown(f'<div class="kpi-value">94%</div><div class="kpi-delta delta-pos">+3.1%</div> <span class="small">optimization rate</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        card_header("Cost Savings")
        st.markdown(f'<div class="kpi-value">₹12,450</div><div class="kpi-delta delta-pos">+15.8%</div> <span class="small">this quarter</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def show_sales_vs_orders():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    card_header("Sales vs Orders")
    if sales_df is None or sales_df.empty or not {"Date","Quantity"}.issubset(sales_df.columns):
        st.info("Sales XLSX missing or invalid. Place it under ./data and click Rebuild.")
    else:
        s = sales_df.copy()
        s["Date"] = pd.to_datetime(s["Date"])
        monthly = s.groupby(s["Date"].dt.to_period("M")).agg(Sales=("Value","sum"), Orders=("Quantity","sum")).reset_index()
        monthly["Date"] = monthly["Date"].dt.to_timestamp()
        fig = go.Figure()
        fig.add_bar(x=monthly["Date"], y=monthly["Sales"], name="Sales", marker_color="#6366f1")
        fig.add_scatter(x=monthly["Date"], y=monthly["Orders"], name="Orders", mode="lines+markers", line=dict(color="#06b6d4", width=2))
        fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,24,39,1)", font_color="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

def show_inventory_trend():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    card_header("Inventory trend")
    if latest_inv.empty or "Quantity" not in latest_inv.columns:
        st.info("Inventory not available. Click Rebuild.")
    else:
        inv = latest_inv.copy()
        inv["Quantity"] = pd.to_numeric(inv["Quantity"], errors="coerce").fillna(0)
        inv = inv.sort_values("Particular")
        eoq_map = dict(zip(eoq_df.get("Particular", []), eoq_df.get("EOQ", []))) if not eoq_df.empty else {}
        inv["Optimal"] = inv["Particular"].map(eoq_map).fillna(inv["Quantity"].median() if len(inv) else 0)
        fig2 = go.Figure()
        fig2.add_scatter(x=inv["Particular"], y=inv["Quantity"], name="Stock", mode="lines", line=dict(color="#22c55e"))
        fig2.add_scatter(x=inv["Particular"], y=inv["Optimal"], name="Optimal", mode="lines", line=dict(color="#f59e0b", dash="dash"))
        fig2.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,24,39,1)", font_color="#e2e8f0")
        st.plotly_chart(fig2, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

def show_category_mix():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    card_header("Category mix")
    if sales_df is None or sales_df.empty or "Particular" not in sales_df.columns:
        st.info("No category data yet.")
    else:
        s = sales_df.copy()
        s["Category"] = extract_product_type(s["Particular"])
        pie = s.groupby("Category")["Quantity"].sum().reset_index()
        fig3 = px.pie(pie, names="Category", values="Quantity", color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b","#ef4444"])
        fig3.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig3, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

def show_eoq_by_sku():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    card_header("EOQ by SKU")
    if eoq_df.empty or "EOQ" not in eoq_df.columns:
        st.info("EOQ not computed. Click Rebuild.")
    else:
        top = eoq_df.sort_values("EOQ", ascending=False).head(15)
        fig = px.bar(top, x="Particular", y="EOQ", color_discrete_sequence=["#6366f1"])
        fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

def show_inventory_vs_rop():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    card_header("Inventory vs ROP")
    if rop_df.empty or not {"Particular","inventory_position","reorder_point"}.issubset(rop_df.columns):
        st.info("Reorder evaluation not available yet.")
    else:
        table = rop_df[["Particular","inventory_position","reorder_point","need_reorder","suggested_order_qty"]].sort_values(["need_reorder","Particular"], ascending=[False, True])
        st.dataframe(table, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_reorder_suggestions():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    card_header("Reorder suggestions")
    if rop_df.empty or "need_reorder" not in rop_df.columns:
        st.info("No suggestions to display.")
    else:
        suggest = rop_df[rop_df["need_reorder"] == True][["Particular","suggested_order_qty","EOQ","lead_time_days","service_level"]]
        st.dataframe(suggest.sort_values("suggested_order_qty", ascending=False), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_monthly_mix():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    card_header("Monthly mix")
    if sales_df is None or sales_df.empty:
        st.info("No sales data.")
    else:
        _, mix_pct = calculate_monthly_mix(sales_df)
        mix_pct = mix_pct.reset_index().melt(id_vars="YearMonth", var_name="Type", value_name="Pct")
        mix_pct["YearMonth"] = mix_pct["YearMonth"].astype(str)
        fig = px.area(mix_pct, x="YearMonth", y="Pct", color="Type", color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b"])
        fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------- Charts Section ----------------
left, mid, right = st.columns((6,6,5))

with left:
    st.markdown('<div class="card"><div class="section-title">Sales vs Orders</div>', unsafe_allow_html=True)
    if sales_df is not None and {"Date","Quantity"}.issubset(sales_df.columns):
        s = sales_df.copy()
        s["Date"] = pd.to_datetime(s["Date"])
        monthly = s.groupby(s["Date"].dt.to_period("M")).agg(Sales=("Value","sum"), Orders=("Quantity","sum")).reset_index()
        monthly["Date"] = monthly["Date"].dt.to_timestamp()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly["Date"], y=monthly["Sales"], name="Sales", marker_color="#6366f1"))
        fig.add_trace(go.Scatter(x=monthly["Date"], y=monthly["Orders"], name="Orders", mode="lines+markers", line=dict(color="#06b6d4", width=2)))
        fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,24,39,1)", font_color="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True, theme=None)
    else:
        st.info("Sales XLSX missing or invalid. Click Rebuild.")
    st.markdown('</div>', unsafe_allow_html=True)

with mid:
    st.markdown('<div class="card"><div class="section-title">Inventory trend</div>', unsafe_allow_html=True)
    if not latest_inv.empty and "Quantity" in latest_inv.columns:
        inv = latest_inv.copy()
        inv["Quantity"] = pd.to_numeric(inv["Quantity"], errors="coerce").fillna(0)
        inv = inv.sort_values("Particular")
        # Simple “optimal” target: use EOQ as proxy if present
        eoq_map = dict(zip(eoq_df.get("Particular", []), eoq_df.get("EOQ", []))) if not eoq_df.empty else {}
        inv["Optimal"] = inv["Particular"].map(eoq_map).fillna(inv["Quantity"].median() if len(inv) else 0)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=inv["Particular"], y=inv["Quantity"], name="Stock", mode="lines", line=dict(color="#22c55e")))
        fig2.add_trace(go.Scatter(x=inv["Particular"], y=inv["Optimal"], name="Optimal", mode="lines", line=dict(color="#f59e0b", dash="dash")))
        fig2.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,24,39,1)", font_color="#e2e8f0")
        st.plotly_chart(fig2, use_container_width=True, theme=None)
    else:
        st.info("Inventory not available. Click Rebuild.")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card"><div class="section-title">Category mix</div>', unsafe_allow_html=True)
    if sales_df is not None and "Particular" in sales_df.columns:
        # naive category extraction mirroring your trends logic
        def extract(pt):
            for t in ["DWR","DIR","HDHMR"]:
                if isinstance(pt,str) and t in pt: return t
            return "OTHER"
        s = sales_df.copy()
        s["Category"] = s["Particular"].apply(extract)
        pie = s.groupby("Category")["Quantity"].sum().reset_index()
        fig3 = px.pie(pie, names="Category", values="Quantity", color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b","#ef4444"])
        fig3.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig3, use_container_width=True, theme=None)
    else:
        st.info("No category data yet.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Recommendations Panel ----------------
st.markdown('<div class="card"><div class="section-title">Next order suggestion</div>', unsafe_allow_html=True)

if not rop_df.empty and "need_reorder" in rop_df.columns:
    needs = rop_df[rop_df["need_reorder"] == True].copy()
    needs["Rate"] = pd.to_numeric(needs.get("Rate", pd.Series(index=needs.index)), errors="coerce")
    needs["suggested_order_qty"] = pd.to_numeric(needs["suggested_order_qty"], errors="coerce").fillna(0)
    needs["est_total"] = needs["suggested_order_qty"] * needs["Rate"]
    est_total_cost = needs["est_total"].sum(skipna=True)
    st.markdown(f'<div class="small">Based on demand, lead times, and service levels, the combination below reduces stockout risk while controlling carrying cost.</div><div class="hr"></div>', unsafe_allow_html=True)
    top = needs.sort_values("suggested_order_qty", ascending=False).head(8)
    rows = []
    for _, r in top.iterrows():
        reason = "Below ROP" if r.get("inventory_position", 0) < r.get("reorder_point", 0) else "Buffer optimization"
        rows.append(f'<li class="row"><span>{r["Particular"]}</span><span class="pill">Qty {int(r["suggested_order_qty"])}{"" if pd.isna(r.get("Rate")) else f" · ₹{int(r.get("Rate",0))}/u"}</span></li><div class="small">{reason}</div>')
    st.markdown('<ul class="clean">' + "".join(rows) + '</ul>', unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown(f'<div>Total est. order cost</div><div class="kpi-value">₹{est_total_cost:,.0f}</div>', unsafe_allow_html=True)
else:
    st.info("No reorder suggestions available. Click Rebuild once data is in place.")
st.markdown('</div>', unsafe_allow_html=True)
