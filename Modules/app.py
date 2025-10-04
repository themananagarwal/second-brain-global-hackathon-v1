# test.py
import os
import math
import pandas as pd
import plotly.express as px
import streamlit as st

# Local modules
from data_ingestion import load_sales_data, append_daily_sales
from inventory_tracker import build_inventory_timeline
from rolling_eoq import calculate_rolling_eoq
from reorder_evaluator import evaluate_reorder_points

# ------------- Streamlit page config -------------
st.set_page_config(page_title="Inventory & Replenishment", page_icon="📦", layout="wide")  # [attached_file:35]

# ------------- Paths and constants -------------
DATA_DIR = "data"
SALES_XLSX = os.path.join(DATA_DIR, "MDF Sales data.xlsx")
PURCHASE_XLSX = os.path.join(DATA_DIR, "MDF purchase data.xlsx")
BASE_INV_XLSX = os.path.join(DATA_DIR, "inventory Base Data.xlsx")
LATEST_INV_CSV = os.path.join(DATA_DIR, "latest_inventory.csv")
EOQ_OUT_CSV = os.path.join("outputs", "eoq_results.csv")
REORDER_EVAL_CSV = os.path.join("data", "reorder_evaluation.csv")  # produced by evaluate_reorder_points  # [attached_file:39][attached_file:42]

os.makedirs("outputs", exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ------------- Sidebar inputs -------------
st.sidebar.header("Parameters")  # [attached_file:35]
lookback_days = st.sidebar.number_input("Lookback days (demand)", min_value=30, max_value=365, value=120, step=10)  # [attached_file:37][attached_file:39]
default_lead_time = st.sidebar.number_input("Default lead time (days)", min_value=1, max_value=60, value=7, step=1)  # [attached_file:39]
default_service = st.sidebar.selectbox("Default service level", options=[0.90, 0.95, 0.975, 0.99], index=1)  # [attached_file:39]
min_safety = st.sidebar.number_input("Min safety stock (units)", min_value=0, value=10, step=5)  # [attached_file:39]
min_rop = st.sidebar.number_input("Min reorder point (units)", min_value=0, value=20, step=5)  # [attached_file:39]

st.sidebar.markdown("---")
run_refresh = st.sidebar.button("Rebuild inventory and recompute EOQ/ROP")  # [attached_file:35]

# ------------- Helper for safe metrics -------------
def safe_metric_value(value, suffix=""):
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{value:,.0f}{suffix}"
    return str(value)  # [attached_file:35]

# ------------- Data pipeline orchestration -------------
@st.cache_data(show_spinner=False)
def load_sales():
    # Expect XLSX with Date/Particular/Quantity
    df = load_sales_data(SALES_XLSX, sheet_name="Sheet1")
    return df  # [attached_file:43]

def rebuild_inventory():
    inv_timeline, latest_inv = build_inventory_timeline(
        sales_file=SALES_XLSX,
        purchase_file=PURCHASE_XLSX,
        base_inventory_file=BASE_INV_XLSX,
    )
    latest_inv.to_csv(LATEST_INV_CSV, index=False)
    return inv_timeline, latest_inv  # [attached_file:42]

def compute_eoq(sales_df):
    # SKU weights mapping; adjust as needed or load from a CSV
    sku_weights = {}  # e.g., {"11MM DWR": 30, "18MM DWR": 45}
    eoq_df = calculate_rolling_eoq(sales_df, sku_weights=sku_weights, lookback_days=lookback_days)
    os.makedirs(os.path.dirname(EOQ_OUT_CSV), exist_ok=True)
    eoq_df.to_csv(EOQ_OUT_CSV, index=False)
    return eoq_df  # [attached_file:37]

def compute_reorder(sales_file, inventory_file, eoq_file):
    df = evaluate_reorder_points(
        sales_file=sales_file,
        inventory_file=inventory_file,
        eoq_file=eoq_file,
        sheet_name="Sheet1",
        lookback_days=lookback_days,
        default_lead_time_days=default_lead_time,
        default_service_level=default_service,
        onorder_file=None,
        backorders_file=None,
        min_safety_stock=min_safety,
        min_reorder_point=min_rop,
    )
    return df  # [attached_file:39]

# ------------- Run/refresh -------------
if run_refresh:
    with st.spinner("Rebuilding inventory and computing EOQ/ROP..."):
        inv_timeline, latest_inv = rebuild_inventory()
        sales_df = load_sales()
        eoq_df = compute_eoq(sales_df)
        rop_df = compute_reorder(SALES_XLSX, LATEST_INV_CSV, EOQ_OUT_CSV)
    st.success("Data recomputed.")  # [attached_file:42][attached_file:37][attached_file:39]

# ------------- Load artifacts (lazy) -------------
def try_load_csv(path, empty_cols=None):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=empty_cols or [])  # [attached_file:42][attached_file:39]

sales_df = None
try:
    sales_df = load_sales()
except Exception:
    pass  # [attached_file:43]

latest_inv = try_load_csv(LATEST_INV_CSV, empty_cols=["Particular", "Quantity"])  # [attached_file:42]
eoq_df = try_load_csv(EOQ_OUT_CSV, empty_cols=["Particular", "dailydemand", "annualdemand", "EOQ", "unitweight", "orderingcost", "holdingcost"])  # [attached_file:37]
rop_df = try_load_csv(REORDER_EVAL_CSV, empty_cols=[
    "Particular","mudaily","sigmadaily","leadtimedays","servicelevel","Z",
    "leadtimedemand","safetystock","reorderpoint","currentinventory","onorder",
    "backorders","inventoryposition","EOQ","needreorder","suggestedorderqty"
])  # [attached_file:39]

# ------------- Header -------------
st.markdown("### Inventory dashboard")  # [attached_file:35]

# ------------- Top KPIs -------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    total_skus = latest_inv["Particular"].nunique() if not latest_inv.empty else 0
    st.metric("Tracked SKUs", safe_metric_value(total_skus))  # [attached_file:42]
with k2:
    need_reorder = int(rop_df["needreorder"].sum()) if "needreorder" in rop_df else 0
    st.metric("SKUs to reorder", safe_metric_value(need_reorder))  # [attached_file:39]
with k3:
    total_eoq_units = int(eoq_df["EOQ"].sum()) if "EOQ" in eoq_df else 0
    st.metric("Total EOQ units", safe_metric_value(total_eoq_units))  # [attached_file:37]
with k4:
    avg_lead = float(rop_df["leadtimedays"].mean()) if "leadtimedays" in rop_df and not rop_df.empty else 0
    st.metric("Avg lead time (d)", safe_metric_value(avg_lead))  # [attached_file:39]

# ------------- Charts row -------------
c1, c2 = st.columns((7, 6))
with c1:
    st.subheader("Sales/Orders trend")
    if sales_df is not None and not sales_df.empty and all(col in sales_df.columns for col in ["Date", "Particular", "Quantity"]):
        daily = sales_df.copy()
        daily["Date"] = pd.to_datetime(daily["Date"])
        trend = daily.groupby(daily["Date"].dt.to_period("M"))["Quantity"].sum().reset_index()
        trend["Date"] = trend["Date"].dt.to_timestamp()
        fig = px.line(trend, x="Date", y="Quantity", markers=True)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")  # [attached_file:43]
    else:
        st.info("Sales data not available. Provide XLSX with Date/Particular/Quantity.")  # [attached_file:43]
with c2:
    st.subheader("EOQ by SKU")
    if not eoq_df.empty:
        top = eoq_df.sort_values("EOQ", ascending=False).head(15)
        fig2 = px.bar(top, x="Particular", y="EOQ")
        fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig2, use_container_width=True, theme="streamlit")  # [attached_file:37]
    else:
        st.info("EOQ not computed yet. Click refresh after placing input files.")  # [attached_file:37]

# ------------- Inventory status + Recommendations -------------
l1, l2 = st.columns((7, 7))
with l1:
    st.subheader("Inventory vs ROP")
    if not rop_df.empty:
        show = rop_df[["Particular","inventoryposition","reorderpoint","needreorder","suggestedorderqty"]].copy()
        show = show.sort_values(["needreorder","Particular"], ascending=[False, True])
        st.dataframe(show, use_container_width=True)
    else:
        st.info("Reorder evaluation not available. Click refresh.")  # [attached_file:39]

with l2:
    st.subheader("Reorder suggestions")
    if not rop_df.empty:
        suggest = rop_df[rop_df["needreorder"] == True][["Particular","suggestedorderqty","EOQ","leadtimedays","servicelevel"]]
        st.dataframe(suggest.sort_values("suggestedorderqty", ascending=False), use_container_width=True)  # [attached_file:39]
    else:
        st.info("No suggestions yet.")  # [attached_file:39]

# ------------- Footer -------------
st.caption("Place input Excel files in ./data and use the sidebar to recompute.")  # [attached_file:42][attached_file:43]
