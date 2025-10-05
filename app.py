# app.py
import os
from io import StringIO
from contextlib import redirect_stdout
import importlib
import importlib.util

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from Modules.data_ingestion import load_sales_data
from Modules.inventory_tracker import build_inventory_timeline
from Modules.rolling_eoq import calculate_rolling_eoq
from Modules.reorder_evaluator import evaluate_reorder_points
from Modules.trends_analysis import calculate_monthly_mix
import template as tpl  # design & rendering layer

# ---------- Page ----------
st.set_page_config(page_title="Inventory & Orders", layout="wide")

# ---------- Paths ----------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("outputs", exist_ok=True)

SALES_XLSX = os.path.join(DATA_DIR, "MDF Sales data.xlsx")
PURCHASE_XLSX = os.path.join(DATA_DIR, "MDF purchase data.xlsx")
BASE_INV_XLSX = os.path.join(DATA_DIR, "Inventory Base Data.xlsx")

LATEST_INV_CSV = os.path.join(DATA_DIR, "latest_inventory.csv")
EOQ_OUT_CSV = os.path.join("outputs", "eoq_results.csv")
REORDER_EVAL_CSV = os.path.join(DATA_DIR, "reorder_evaluation.csv")

# ---------- Styles ----------
tpl.inject_css()

# ---------- Sidebar Controls ----------
st.sidebar.header("Controls")
lookback_days = st.sidebar.number_input("Demand lookback (days)", 30, 365, 365, 10)
default_lead_time = st.sidebar.number_input("Default lead time (days)", 1, 60, 7, 1)
default_service = st.sidebar.selectbox("Default service level", [0.90, 0.95, 0.975, 0.99], 1)
min_safety = st.sidebar.number_input("Min safety stock", 0, 10000, 10, 5)
min_rop = st.sidebar.number_input("Min reorder point", 0, 10000, 20, 5)
rebuild = st.sidebar.button("Rebuild inventory + recompute EOQ/ROP")

st.sidebar.markdown("---")
st.sidebar.subheader("Dashboard sections")
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

# ---------- Data helpers ----------
@st.cache_data(show_spinner=False)
def load_sales():
    return load_sales_data(SALES_XLSX, sheet_name="Sheet1")

def try_read_csv(path, cols=None):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=cols or [])

def compute_pipeline():
    # Build inventory timeline and persist stock snapshot
    inv_timeline, latest_inv = build_inventory_timeline(
        sales_file=SALES_XLSX,
        purchase_file=PURCHASE_XLSX,
        base_inventory_file=BASE_INV_XLSX,
    )
    latest_inv.to_csv(LATEST_INV_CSV, index=False)

    # Sales
    sales_df = load_sales()
    sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")

    # SKU weights for EOQ
    sku_weights = dict(zip(sales_df["Particular"], sales_df["Weight Per Piece"])) if "Weight Per Piece" in sales_df.columns else {}

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

    # Monthly mix for area chart
    _, mix_pct = calculate_monthly_mix(sales_df)

    return inv_timeline, latest_inv, sales_df, eoq_df, rop_df, mix_pct

# ---------- Load or compute ----------
if rebuild:
    with st.spinner("Recomputing…"):
        inv_timeline, latest_inv, sales_df, eoq_df, rop_df, mix_pct = compute_pipeline()
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
    if sales_df is not None and not sales_df.empty and "Date" in sales_df.columns and "Particular" in sales_df.columns:
        _, mix_pct = calculate_monthly_mix(sales_df)
    else:
        mix_pct = pd.DataFrame()

# ---------- Simulation integration ----------
if "sim_running" not in st.session_state:
    st.session_state["sim_running"] = False

def _load_simulation_module():
    # 1) Preferred: Modules.simulation
    try:
        from Modules import simulation  # type: ignore
        return simulation
    except Exception:
        pass
    # 2) Fallback: simulation in project root
    try:
        import simulation  # type: ignore
        return simulation
    except Exception:
        pass
    # 3) Fallback: explicit path under Modules
    sim_path = os.path.join("Modules", "simulation.py")
    if os.path.exists(sim_path):
        spec = importlib.util.spec_from_file_location("simulation", sim_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    raise ImportError("simulation.py not found in Modules/ or project root")

# ---------- Tabs ----------
home_tab, dash_tab = st.tabs(["Home", "Dashboard"])

with home_tab:
    tpl.render_home()

with dash_tab:
    # Centered “Run simulation” button; disabled while running; shows results on completion
    clicked = tpl.simulation_bar_centered(disabled=st.session_state["sim_running"])
    if clicked and not st.session_state["sim_running"]:
        st.session_state["sim_running"] = True
        log_buf = StringIO()
        try:
            sim = _load_simulation_module()
            with st.spinner("Running simulation..."):
                with redirect_stdout(log_buf):
                    if hasattr(sim, "simulate"):
                        # Run in non-interactive mode for Streamlit
                        sim.simulate(interactive=False)
                    else:
                        print("ERROR: simulate() not found in simulation module")
            st.success("Simulation complete.")
        except Exception as e:
            log_buf.write(f"\nERROR: {e}\n")
            st.error("Simulation failed. See log for details.")
        finally:
            st.session_state["sim_running"] = False

        # Render filterable tables (90‑day slider where applicable) + downloads + raw log
        tpl.simulation_results_panel(log_buf.getvalue(), base_dir="data")

    # Dashboard header
    st.markdown(
        '<div class="section-title" id="dashboard">AI-powered insights for optimized decision making</div>'
        '<div class="small">Drive lower carrying costs and fewer stockouts with data-backed reorder plans.</div>',
        unsafe_allow_html=True
    )

    # Render dashboard sections
    tpl.render_dashboard(
        sales_df=sales_df if sales_df is not None else pd.DataFrame(),
        latest_inv=latest_inv if latest_inv is not None else pd.DataFrame(),
        eoq_df=eoq_df if eoq_df is not None else pd.DataFrame(),
        rop_df=rop_df if rop_df is not None else pd.DataFrame(),
        mix_pct=mix_pct if mix_pct is not None else pd.DataFrame(),
        visible_sections=visible
    )
