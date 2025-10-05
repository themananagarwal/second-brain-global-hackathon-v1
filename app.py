# app.py
import os
from io import StringIO
from contextlib import redirect_stdout  # Fixed typo: was "contextual" should be "contextlib"
import importlib
import importlib.util
import types
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from Modules.data_ingestion import load_sales_data
from Modules.inventory_tracker import build_inventory_timeline
from Modules.rolling_eoq import calculate_rolling_eoq
from Modules.reorder_evaluator import evaluate_reorder_points
from Modules.trends_analysis import calculate_monthly_mix
from template import inject_global_css
from home_page import render_home_page
from dashboard_page import render_dashboard_page

# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="SecondBrain - Inventory Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Global Styles
# =========================
inject_global_css()

# =========================
# Data Paths
# =========================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("outputs", exist_ok=True)

SALES_XLSX = os.path.join(DATA_DIR, "MDF Sales data.xlsx")
PURCHASE_XLSX = os.path.join(DATA_DIR, "MDF purchase data.xlsx")
BASE_INV_XLSX = os.path.join(DATA_DIR, "Inventory Base Data.xlsx")

LATEST_INV_CSV = os.path.join(DATA_DIR, "latest_inventory.csv")
EOQ_OUT_CSV = os.path.join("outputs", "eoq_results.csv")
REORDER_EVAL_CSV = os.path.join(DATA_DIR, "reorder_evaluation.csv")

# =========================
# Session State
# =========================
if "sim_running" not in st.session_state:
    st.session_state["sim_running"] = False
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Home"


# =========================
# Data Helpers
# =========================
@st.cache_data(show_spinner=False)
def load_sales():
    return load_sales_data(SALES_XLSX, sheet_name="Sheet1")


def try_read_csv(path, cols=None):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=cols or [])


def compute_pipeline():
    inv_timeline, latest_inv = build_inventory_timeline(
        sales_file=SALES_XLSX, purchase_file=PURCHASE_XLSX, base_inventory_file=BASE_INV_XLSX
    )
    latest_inv.to_csv(LATEST_INV_CSV, index=False)

    sales_df = load_sales()
    sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")

    sku_weights = dict(
        zip(sales_df["Particular"], sales_df["Weight Per Piece"])) if "Weight Per Piece" in sales_df.columns else {}

    eoq_df = calculate_rolling_eoq(sales_df, sku_weights=sku_weights, lookback_days=365)
    eoq_df.to_csv(EOQ_OUT_CSV, index=False)

    rop_df = evaluate_reorder_points(
        sales_file=SALES_XLSX, inventory_file=LATEST_INV_CSV, eoq_file=EOQ_OUT_CSV,
        sheet_name="Sheet1", lookback_days=365,
        default_lead_time_days=7, default_service_level=0.95,
        on_order_file=None, backorders_file=None,
        min_safety_stock=10, min_reorder_point=20,
    )
    rop_df.to_csv(REORDER_EVAL_CSV, index=False)

    _, mix_pct = calculate_monthly_mix(sales_df)
    return inv_timeline, latest_inv, sales_df, eoq_df, rop_df, mix_pct


# =========================
# Page Navigation
# =========================
st.markdown("""
<div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 2rem; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 1rem;">
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("🏠 Home", use_container_width=True,
                 type="primary" if st.session_state["current_page"] == "Home" else "secondary"):
        st.session_state["current_page"] = "Home"
        st.rerun()

with col2:
    if st.button("📊 Dashboard", use_container_width=True,
                 type="primary" if st.session_state["current_page"] == "Dashboard" else "secondary"):
        st.session_state["current_page"] = "Dashboard"
        st.rerun()

with col3:
    if st.button("📦 Inventory", use_container_width=True,
                 type="primary" if st.session_state["current_page"] == "Inventory" else "secondary"):
        st.session_state["current_page"] = "Inventory"
        st.rerun()

# =========================
# Page Routing
# =========================
if st.session_state["current_page"] == "Home":
    render_home_page()
elif st.session_state["current_page"] == "Dashboard":
    # Load data for dashboard
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
                           "lead_time_days", "service_level", "Rate"])

    if sales_df is not None and not sales_df.empty and "Date" in sales_df.columns and "Particular" in sales_df.columns:
        _, mix_pct = calculate_monthly_mix(sales_df)
    else:
        mix_pct = pd.DataFrame()

    render_dashboard_page(
        sales_df=sales_df if sales_df is not None else pd.DataFrame(),
        latest_inv=latest_inv if latest_inv is not None else pd.DataFrame(),
        eoq_df=eoq_df if eoq_df is not None else pd.DataFrame(),
        rop_df=rop_df if rop_df is not None else pd.DataFrame(),
        mix_pct=mix_pct if mix_pct is not None else pd.DataFrame()
    )
elif st.session_state["current_page"] == "Inventory":
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title" style="font-size: 3rem;">Inventory Management</div>
        <div class="hero-subtitle">Advanced inventory tracking and management tools - Coming Soon</div>
        <div style="margin-top: 2rem;">
            <div class="btn btn-secondary" style="background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.3); color: white;">
                🚧 Under Development
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
