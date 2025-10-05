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

from Modules.data_ingestion import load_sales_data  # data loading [attached_file:7]
from Modules.inventory_tracker import build_inventory_timeline  # inventory timeline [attached_file:4]
from Modules.rolling_eoq import calculate_rolling_eoq  # EOQ engine [attached_file:6]
from Modules.reorder_evaluator import evaluate_reorder_points  # ROP engine [attached_file:10]
from Modules.trends_analysis import calculate_monthly_mix  # monthly mix [attached_file:13]

# Robust design-module import (template.py can live in Modules/ or project root) [attached_file:9]
try:
    from Modules import template as tpl  # if template.py is under Modules/ [attached_file:9]
except Exception:
    import template as tpl               # else expect template.py at project root [attached_file:9]

# Fail fast if the design module doesn’t have required renderers [attached_file:9]
REQUIRED_FUNCS = [
    "inject_css",
    "render_home",
    "simulation_bar_centered",
    "simulation_results_panel",
    "render_dashboard",
]
missing = [f for f in REQUIRED_FUNCS if not hasattr(tpl, f)]
if missing:
    st.error(f"Design module missing: {', '.join(missing)}. Ensure template.py defines these functions.")  # guard [attached_file:9]
    st.stop()  # stop early if template is incomplete [attached_file:9]

# ---------- Page ---------- #
st.set_page_config(page_title="Inventory & Orders", layout="wide")  # wide layout for dashboard [attached_file:9]

# ---------- Paths ---------- #
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)  # ensure data dir exists [attached_file:9]
os.makedirs("outputs", exist_ok=True)  # ensure outputs dir exists [attached_file:9]

SALES_XLSX = os.path.join(DATA_DIR, "MDF Sales data.xlsx")  # sales input path [attached_file:9]
PURCHASE_XLSX = os.path.join(DATA_DIR, "MDF purchase data.xlsx")  # purchase input path [attached_file:9]
BASE_INV_XLSX = os.path.join(DATA_DIR, "Inventory Base Data.xlsx")  # base inventory path [attached_file:9]

LATEST_INV_CSV = os.path.join(DATA_DIR, "latest_inventory.csv")  # latest inventory snapshot [attached_file:9]
EOQ_OUT_CSV = os.path.join("outputs", "eoq_results.csv")  # EOQ results path [attached_file:9]
REORDER_EVAL_CSV = os.path.join(DATA_DIR, "reorder_evaluation.csv")  # ROP results path [attached_file:9]

# ---------- Styles ---------- #
tpl.inject_css()  # inject global CSS for spacing, cards, modebar, etc. [attached_file:9]

# ---------- Sidebar Controls ---------- #
st.sidebar.header("Controls")  # sidebar control header [attached_file:9]
lookback_days = st.sidebar.number_input("Demand lookback (days)", 30, 365, 365, 10)  # lookback [attached_file:9]
default_lead_time = st.sidebar.number_input("Default lead time (days)", 1, 60, 7, 1)  # lead time [attached_file:9]
default_service = st.sidebar.selectbox("Default service level", [0.90, 0.95, 0.975, 0.99], 1)  # service level [attached_file:9]
min_safety = st.sidebar.number_input("Min safety stock", 0, 10000, 10, 5)  # min SS [attached_file:9]
min_rop = st.sidebar.number_input("Min reorder point", 0, 10000, 20, 5)  # min ROP [attached_file:9]
rebuild = st.sidebar.button("Rebuild inventory + recompute EOQ/ROP")  # pipeline trigger [attached_file:9]

st.sidebar.markdown("---")  # divider [attached_file:9]
st.sidebar.subheader("Dashboard sections")  # sections header [attached_file:9]
ALL_SECTIONS = [
    "KPIs",
    "Sales vs Orders",
    "Inventory trend",
    "Category mix",
    "EOQ by SKU",
    "Inventory vs ROP",
    "Reorder suggestions",
    "Monthly mix",
]  # selectable dashboard sections [attached_file:9]
visible = st.sidebar.multiselect("Show sections", ALL_SECTIONS, default=ALL_SECTIONS)  # visible selection [attached_file:9]

# ---------- Data helpers ---------- #
@st.cache_data(show_spinner=False)
def load_sales():
    return load_sales_data(SALES_XLSX, sheet_name="Sheet1")  # cached sales load [attached_file:7]

def try_read_csv(path, cols=None):
    try:
        return pd.read_csv(path)  # safe csv read [attached_file:9]
    except Exception:
        return pd.DataFrame(columns=cols or [])  # empty df with columns [attached_file:9]

def compute_pipeline():
    # Build inventory timeline and persist current snapshot [attached_file:4]
    inv_timeline, latest_inv = build_inventory_timeline(
        sales_file=SALES_XLSX,
        purchase_file=PURCHASE_XLSX,
        base_inventory_file=BASE_INV_XLSX,
    )  # timeline build [attached_file:4]
    latest_inv.to_csv(LATEST_INV_CSV, index=False)  # persist latest stocks [attached_file:9]

    # Sales preparation [attached_file:7]
    sales_df = load_sales()
    sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")  # ensure datetime [attached_file:9]

    # EOQ weights from sales file if present [attached_file:6]
    sku_weights = dict(zip(sales_df["Particular"], sales_df["Weight Per Piece"])) if "Weight Per Piece" in sales_df.columns else {}  # weights map [attached_file:6]

    # EOQ calculation over lookback [attached_file:6]
    eoq_df = calculate_rolling_eoq(
        sales_df,
        sku_weights=sku_weights,
        lookback_days=lookback_days
    )  # EOQ compute [attached_file:6]
    eoq_df.to_csv(EOQ_OUT_CSV, index=False)  # save EOQ [attached_file:9]

    # ROP / safety stock evaluation with defaults and mins [attached_file:10]
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
    )  # ROP compute [attached_file:10]
    rop_df.to_csv(REORDER_EVAL_CSV, index=False)  # save ROP [attached_file:9]

    # Monthly mix for area chart [attached_file:13]
    _, mix_pct = calculate_monthly_mix(sales_df)  # monthly mix calc [attached_file:13]

    return inv_timeline, latest_inv, sales_df, eoq_df, rop_df, mix_pct  # pipeline outputs [attached_file:9]

# ---------- Load or compute ---------- #
if rebuild:
    with st.spinner("Recomputing…"):
        inv_timeline, latest_inv, sales_df, eoq_df, rop_df, mix_pct = compute_pipeline()  # run pipeline [attached_file:9]
        st.success("Done.")  # success toast [attached_file:9]
else:
    sales_df = None  # default [attached_file:9]
    try:
        sales_df = load_sales()  # cached load [attached_file:7]
        sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")  # ensure datetime [attached_file:9]
    except Exception:
        pass  # tolerate missing file [attached_file:9]
    latest_inv = try_read_csv(LATEST_INV_CSV, ["Particular","Quantity"])  # load latest inv [attached_file:9]
    eoq_df     = try_read_csv(EOQ_OUT_CSV, ["Particular","EOQ"])  # load EOQ [attached_file:9]
    rop_df     = try_read_csv(REORDER_EVAL_CSV, ["Particular","reorder_point","inventory_position","need_reorder","suggested_order_qty","lead_time_days","service_level","Rate"])  # load ROP [attached_file:9]
    if sales_df is not None and not sales_df.empty and "Date" in sales_df.columns and "Particular" in sales_df.columns:
        _, mix_pct = calculate_monthly_mix(sales_df)  # compute mix if sales present [attached_file:13]
    else:
        mix_pct = pd.DataFrame()  # empty mix [attached_file:9]

# ---------- Simulation integration ---------- #
if "sim_running" not in st.session_state:
    st.session_state["sim_running"] = False  # gate to disable button [attached_file:9]

def _load_simulation_module():
    # 1) Preferred: Modules.simulation [attached_file:108]
    try:
        from Modules import simulation  # type: ignore
        return simulation  # module ref [attached_file:108]
    except Exception:
        pass  # fallback next [attached_file:108]
    # 2) Fallback: simulation in project root [attached_file:108]
    try:
        import simulation  # type: ignore
        return simulation  # module ref [attached_file:108]
    except Exception:
        pass  # fallback next [attached_file:108]
    # 3) Fallback: explicit path under Modules [attached_file:108]
    sim_path = os.path.join("Modules", "simulation.py")
    if os.path.exists(sim_path):
        spec = importlib.util.spec_from_file_location("simulation", sim_path)  # load by path [attached_file:108]
        mod = importlib.util.module_from_spec(spec)  # module instance [attached_file:108]
        assert spec and spec.loader  # safety [attached_file:108]
        spec.loader.exec_module(mod)  # type: ignore  # execute module [attached_file:108]
        return mod  # module ref [attached_file:108]
    raise ImportError("simulation.py not found in Modules/ or project root")  # explicit error [attached_file:108]

# ---------- Tabs ---------- #
home_tab, dash_tab = st.tabs(["Home", "Dashboard"])  # top tabs navigation [attached_file:9]

with home_tab:
    tpl.render_home()  # landing page hero & help [attached_file:9]

with dash_tab:
    # Centered “Run simulation” button; disabled while running; shows results on completion [attached_file:9]
    clicked = tpl.simulation_bar_centered(disabled=st.session_state["sim_running"])  # centered CTA [attached_file:9]
    if clicked and not st.session_state["sim_running"]:
        st.session_state["sim_running"] = True  # lock button [attached_file:9]
        log_buf = StringIO()  # capture stdout [attached_file:108]
        try:
            sim = _load_simulation_module()  # resolve module [attached_file:108]
            with st.spinner("Running simulation..."):
                with redirect_stdout(log_buf):  # capture prints [attached_file:108]
                    if hasattr(sim, "simulate"):
                        sim.simulate(interactive=False)  # non-interactive, writes CSVs to data/ [attached_file:108]
                    else:
                        print("ERROR: simulate() not found in simulation module")  # guard [attached_file:108]
            st.success("Simulation complete.")  # success toast [attached_file:9]
        except Exception as e:
            log_buf.write(f"\nERROR: {e}\n")  # write error to log [attached_file:108]
            st.error("Simulation failed. See log for details.")  # user notice [attached_file:9]
        finally:
            st.session_state["sim_running"] = False  # unlock button [attached_file:9]

        # Render filterable tables (90‑day slider where applicable) + downloads + raw log [attached_file:9]
        tpl.simulation_results_panel(log_buf.getvalue(), base_dir="data")  # results tabs [attached_file:9]

    # Dashboard header [attached_file:9]
    st.markdown(
        '<div class="section-title" id="dashboard">AI-powered insights for optimized decision making</div>'
        '<div class="small">Drive lower carrying costs and fewer stockouts with data-backed reorder plans.</div>',
        unsafe_allow_html=True
    )  # header text [attached_file:9]

    # Render dashboard sections with a safety net to surface design errors [attached_file:9]
    try:
        tpl.render_dashboard(
            sales_df=sales_df if sales_df is not None else pd.DataFrame(),
            latest_inv=latest_inv if latest_inv is not None else pd.DataFrame(),
            eoq_df=eoq_df if eoq_df is not None else pd.DataFrame(),
            rop_df=rop_df if rop_df is not None else pd.DataFrame(),
            mix_pct=mix_pct if mix_pct is not None else pd.DataFrame(),
            visible_sections=visible
        )  # delegate to template renderer [attached_file:9]
    except Exception as e:
        st.error("Dashboard rendering failed. Check template.render_dashboard implementation.")  # explicit message [attached_file:9]
        st.code(str(e))  # show exception string for debugging [attached_file:9]
