import os
import pandas as pd
import plotly.express as px
import streamlit as st

# Local modules (package is 'Modules', as in your tree)
from Modules.data_ingestion import load_sales_data
from Modules.inventory_tracker import build_inventory_timeline
from Modules.rolling_eoq import calculate_rolling_eoq
from Modules.reorder_evaluator import evaluate_reorder_points

# ---------------- Page setup ----------------
st.set_page_config(page_title="Inventory & Orders", layout="wide")

# ---------------- Paths ----------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("outputs", exist_ok=True)

SALES_XLSX = os.path.join(DATA_DIR, "MDF Sales data.xlsx")
PURCHASE_XLSX = os.path.join(DATA_DIR, "MDF purchase data.xlsx")
BASE_INV_XLSX = os.path.join(DATA_DIR, "Inventory Base Data.xlsx")

# Inventory tracker writes a latest-inventory CSV; keep it in ./data
LATEST_INV_CSV = os.path.join(DATA_DIR, "latest_inventory.csv")
EOQ_OUT_CSV = os.path.join("outputs", "eoq_results.csv")
REORDER_EVAL_CSV = os.path.join(DATA_DIR, "reorder_evaluation.csv")

# ---------------- Sidebar controls ----------------
st.sidebar.header("Controls")
lookback_days = st.sidebar.number_input("Demand lookback (days)", 30, 365, 365, 10)
default_lead_time = st.sidebar.number_input("Default lead time (days)", 1, 60, 7, 1)
default_service = st.sidebar.selectbox("Default service level", [0.90, 0.95, 0.975, 0.99], 1)
min_safety = st.sidebar.number_input("Min safety stock", 0, 10000, 10, 5)
min_rop = st.sidebar.number_input("Min reorder point", 0, 10000, 20, 5)
rebuild = st.sidebar.button("Rebuild inventory + recompute EOQ/ROP")


# ---------------- Helpers ----------------
@st.cache_data(show_spinner=False)
def load_sales():
    return load_sales_data(SALES_XLSX, sheet_name="Sheet1")


def rebuild_inventory_and_metrics():
    # Build inventory timeline
    inv_timeline, latest_inv = build_inventory_timeline(
        sales_file=SALES_XLSX,
        purchase_file=PURCHASE_XLSX,
        base_inventory_file=BASE_INV_XLSX,
    )
    latest_inv.to_csv(LATEST_INV_CSV, index=False)

    # Load sales data
    sales_df = load_sales()
    sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")

    # Create SKU weights dictionary from sales data
    sku_weights = dict(zip(sales_df['Particular'], sales_df['Weight Per Piece']))

    # Calculate EOQ with correct parameter names
    eoq_df = calculate_rolling_eoq(
        sales_df,
        sku_weights=sku_weights,
        lookback_days=lookback_days
    )
    eoq_df.to_csv(EOQ_OUT_CSV, index=False)

    # Calculate reorder points with correct parameter names
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


# ---------------- Run pipeline ----------------
if rebuild:
    with st.spinner("Recomputing…"):
        inv_timeline, latest_inv, sales_df, eoq_df, rop_df = rebuild_inventory_and_metrics()
        st.success("Done.")
else:
    # Lazy-load artifacts if present
    sales_df = None
    try:
        sales_df = load_sales()
        sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")
    except Exception:
        pass

    latest_inv = try_read_csv(LATEST_INV_CSV, ["Particular", "Quantity"])
    eoq_df = try_read_csv(EOQ_OUT_CSV, ["Particular", "EOQ"])
    rop_df = try_read_csv(REORDER_EVAL_CSV,
                          ["Particular", "reorder_point", "inventory_position", "need_reorder", "suggested_order_qty",
                           "lead_time_days", "service_level"])

# ---------------- Header ----------------
st.markdown("### Inventory and Ordering Dashboard")

# ---------------- KPI cards ----------------
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Tracked SKUs", f"{latest_inv['Particular'].nunique():,}" if not latest_inv.empty else "0")

with k2:
    need = int(rop_df["need_reorder"].sum()) if "need_reorder" in rop_df.columns else 0
    st.metric("SKUs to reorder", f"{need:,}")

with k3:
    total_eoq = int(eoq_df["EOQ"].sum()) if "EOQ" in eoq_df.columns else 0
    st.metric("Total EOQ units", f"{total_eoq:,}")

with k4:
    avg_lt = float(rop_df["lead_time_days"].mean()) if "lead_time_days" in rop_df.columns and not rop_df.empty else 0
    st.metric("Avg lead time (d)", f"{avg_lt:.1f}")

# ---------------- Charts ----------------
c1, c2 = st.columns((7, 6))

with c1:
    st.subheader("Monthly sales trend")
    if sales_df is not None and not sales_df.empty and {"Date", "Quantity"}.issubset(sales_df.columns):
        s = sales_df.copy()
        s["Date"] = pd.to_datetime(s["Date"])
        m = s.groupby(s["Date"].dt.to_period("M"))["Quantity"].sum().reset_index()
        m["Date"] = m["Date"].dt.to_timestamp()
        fig = px.line(m, x="Date", y="Quantity", markers=True)
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
    else:
        st.info("Sales XLSX missing or invalid. Place it under ./data and click Rebuild.")

with c2:
    st.subheader("EOQ by SKU")
    if not eoq_df.empty and "EOQ" in eoq_df.columns:
        top = eoq_df.sort_values("EOQ", ascending=False).head(15)
        fig2 = px.bar(top, x="Particular", y="EOQ")
        fig2.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True, theme="streamlit")
    else:
        st.info("EOQ not computed. Click Rebuild.")

# ---------------- Tables ----------------
t1, t2 = st.columns((7, 7))

with t1:
    st.subheader("Inventory vs ROP")
    if not rop_df.empty and {"Particular", "inventory_position", "reorder_point"}.issubset(rop_df.columns):
        table = rop_df[
            ["Particular", "inventory_position", "reorder_point", "need_reorder", "suggested_order_qty"]].sort_values(
            ["need_reorder", "Particular"], ascending=[False, True]
        )
        st.dataframe(table, use_container_width=True)
    else:
        st.info("Reorder evaluation not available yet.")

with t2:
    st.subheader("Reorder suggestions")
    if not rop_df.empty and "need_reorder" in rop_df.columns:
        suggest = rop_df[rop_df["need_reorder"] == True][
            ["Particular", "suggested_order_qty", "EOQ", "lead_time_days", "service_level"]]
        st.dataframe(suggest.sort_values("suggested_order_qty", ascending=False), use_container_width=True)
    else:
        st.info("No suggestions to display.")
