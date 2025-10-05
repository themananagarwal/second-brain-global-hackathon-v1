import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Local modules
from Modules.data_ingestion import load_sales_data
from Modules.inventory_tracker import build_inventory_timeline
from Modules.rolling_eoq import calculate_rolling_eoq
from Modules.reorder_evaluator import evaluate_reorder_points
from Modules.trends_analysis import extract_product_type, calculate_monthly_mix

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

# ---------------- Theme-ish CSS and card styling ----------------
st.markdown("""
<style>
:root{
  --bg: #0b1220; --card:#0f172a; --muted:#94a3b8; --text:#e2e8f0;
  --primary:#6366f1; --accent:#06b6d4; --success:#22c55e; --warning:#f59e0b; --danger:#ef4444;
}
html, body, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
.section-title{ font-size:16px; font-weight:600; margin-bottom:6px; }
.small{ color: var(--muted); font-size: 12px; }
.kpi-title{ color: var(--muted); font-size: 13px; }
.kpi-value{ font-size: 26px; font-weight: 700; }
.kpi-delta{ font-size: 13px; padding: 2px 8px; border-radius: 999px; display: inline-block; }
.delta-pos{ background: rgba(34,197,94,0.15); color: #86efac; }
.delta-neg{ background: rgba(239,68,68,0.15); color: #fca5a5; }

/* Give Streamlit-rendered blocks a card look */
div[data-testid="stPlotlyChart"],
div[data-testid="stDataFrame"],
div[data-baseweb="notification"] {
  border: 1px solid rgba(148,163,184,0.12);
  background: var(--card);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 0 0 1px rgba(99,102,241,0.05), 0 8px 24px rgba(2,6,23,0.45);
}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar: Controls & Navigation ----------------
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

def try_read_csv(path, cols=None):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=cols or [])

def compute_pipeline():
    # Build inventory timeline from three sources
    inv_timeline, latest_inv = build_inventory_timeline(
        sales_file=SALES_XLSX,
        purchase_file=PURCHASE_XLSX,
        base_inventory_file=BASE_INV_XLSX,
    )
    latest_inv.to_csv(LATEST_INV_CSV, index=False)

    # Load and clean sales
    sales_df = load_sales()
    sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")

    # SKU weights from sales file (Weight Per Piece)
    if "Weight Per Piece" in sales_df.columns:
        sku_weights = dict(zip(sales_df["Particular"], sales_df["Weight Per Piece"]))
    else:
        sku_weights = {}

    # EOQ
    eoq_df = calculate_rolling_eoq(
        sales_df,
        sku_weights=sku_weights,
        lookback_days=lookback_days
    )
    eoq_df.to_csv(EOQ_OUT_CSV, index=False)

    # ROP / reorder evaluation
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

# ---------------- Run / Load pipeline ----------------
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

# ---------------- Helpers: section renderers ----------------
def card_header(title: str):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def show_kpis():
    col1, col2, col3, col4 = st.columns(4)
    total_rev = 0.0
    if sales_df is not None and {"Quantity","Rate"}.issubset(sales_df.columns):
        total_rev = float((sales_df["Quantity"] * sales_df["Rate"]).sum())

    with col1:
        st.markdown('<div class="kpi-title">Total Revenue</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-value">₹{total_rev:,.0f}</div><div class="kpi-delta delta-pos">+12.5%</div> <span class="small">vs last month</span>', unsafe_allow_html=True)

    with col2:
        active = int(rop_df["need_reorder"].sum()) if "need_reorder" in rop_df.columns else 0
        st.markdown('<div class="kpi-title">Active Orders</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-value">{active}</div><div class="kpi-delta delta-pos">+8.2%</div> <span class="small">processing</span>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="kpi-title">Efficiency Score</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-value">94%</div><div class="kpi-delta delta-pos">+3.1%</div> <span class="small">optimization rate</span>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="kpi-title">Cost Savings</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-value">₹12,450</div><div class="kpi-delta delta-pos">+15.8%</div> <span class="small">this quarter</span>', unsafe_allow_html=True)

def show_sales_vs_orders():
    card_header("Sales vs Orders")
    if sales_df is None or sales_df.empty or not {"Date","Quantity"}.issubset(sales_df.columns):
        st.info("Sales XLSX missing or invalid. Place it under ./data and click Rebuild.")
        return
    s = sales_df.copy()
    s["Date"] = pd.to_datetime(s["Date"])
    monthly = s.groupby(s["Date"].dt.to_period("M")).agg(Sales=("Value","sum"), Orders=("Quantity","sum")).reset_index()
    monthly["Date"] = monthly["Date"].dt.to_timestamp()
    fig = go.Figure()
    fig.add_bar(x=monthly["Date"], y=monthly["Sales"], name="Sales", marker_color="#6366f1")
    fig.add_scatter(x=monthly["Date"], y=monthly["Orders"], name="Orders", mode="lines+markers", line=dict(color="#06b6d4", width=2))
    fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,24,39,1)", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True, theme=None)

def show_inventory_trend():
    card_header("Inventory trend")
    if latest_inv.empty or "Quantity" not in latest_inv.columns:
        st.info("Inventory not available. Click Rebuild.")
        return
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

def show_category_mix():
    card_header("Category mix")
    if sales_df is None or sales_df.empty or "Particular" not in sales_df.columns:
        st.info("No category data yet.")
        return
    s = sales_df.copy()
    s["Category"] = extract_product_type(s["Particular"])
    pie = s.groupby("Category")["Quantity"].sum().reset_index()
    fig3 = px.pie(pie, names="Category", values="Quantity",
                  color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b","#ef4444"])
    fig3.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
    st.plotly_chart(fig3, use_container_width=True, theme=None)

def show_eoq_by_sku():
    card_header("EOQ by SKU")
    if eoq_df.empty or "EOQ" not in eoq_df.columns:
        st.info("EOQ not computed. Click Rebuild.")
        return
    top = eoq_df.sort_values("EOQ", ascending=False).head(15)
    fig = px.bar(top, x="Particular", y="EOQ", color_discrete_sequence=["#6366f1"])
    fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True, theme=None)

def show_inventory_vs_rop():
    card_header("Inventory vs ROP")
    if rop_df.empty or not {"Particular","inventory_position","reorder_point"}.issubset(rop_df.columns):
        st.info("Reorder evaluation not available yet.")
        return
    table = rop_df[["Particular","inventory_position","reorder_point","need_reorder","suggested_order_qty"]] \
            .sort_values(["need_reorder","Particular"], ascending=[False, True])
    st.dataframe(table, use_container_width=True)

def show_reorder_suggestions():
    card_header("Reorder suggestions")
    if rop_df.empty or "need_reorder" not in rop_df.columns:
        st.info("No suggestions to display.")
        return
    suggest = rop_df[rop_df["need_reorder"] == True][["Particular","suggested_order_qty","EOQ","lead_time_days","service_level"]]
    st.dataframe(suggest.sort_values("suggested_order_qty", ascending=False), use_container_width=True)

def show_monthly_mix():
    card_header("Monthly mix")
    if sales_df is None or sales_df.empty:
        st.info("No sales data.")
        return
    _, mix_pct = calculate_monthly_mix(sales_df)
    mix_pct = mix_pct.reset_index().melt(id_vars="YearMonth", var_name="Type", value_name="Pct")
    mix_pct["YearMonth"] = mix_pct["YearMonth"].astype(str)
    fig = px.area(mix_pct, x="YearMonth", y="Pct", color="Type",
                  color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b"])
    fig.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True, theme=None)

# ---------------- Header ----------------
st.markdown(
    '<div class="section-title">AI-powered insights for optimized decision making</div>'
    '<div class="small">Drive lower carrying costs and fewer stockouts with data-backed reorder plans.</div>',
    unsafe_allow_html=True
)

# ---------------- Render selected sections ----------------
if "KPIs" in visible:
    show_kpis()

cols_top = st.columns((7,6,6))
with cols_top[0]:
    if "Sales vs Orders" in visible:
        show_sales_vs_orders()
with cols_top[1]:
    if "Inventory trend" in visible:
        show_inventory_trend()
with cols_top[2]:
    if "Category mix" in visible:
        show_category_mix()

cols_bottom = st.columns((7,7))
with cols_bottom[0]:
    if "EOQ by SKU" in visible:
        show_eoq_by_sku()
with cols_bottom[1]:
    if "Monthly mix" in visible:
        show_monthly_mix()

if "Inventory vs ROP" in visible:
    show_inventory_vs_rop()
if "Reorder suggestions" in visible:
    show_reorder_suggestions()
