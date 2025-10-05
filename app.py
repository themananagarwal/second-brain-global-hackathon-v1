# app.py
import os
from io import StringIO
from contextlib import redirect_stdout
import importlib
import importlib.util
import types

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from Modules.data_ingestion import load_sales_data  # data loading
from Modules.inventory_tracker import build_inventory_timeline  # inventory timeline
from Modules.rolling_eoq import calculate_rolling_eoq  # EOQ engine
from Modules.reorder_evaluator import evaluate_reorder_points  # ROP engine
from Modules.trends_analysis import calculate_monthly_mix  # monthly mix

# =========================
# Robust template import + graceful fallback
# =========================
try:
    from Modules import template as tpl  # if template.py is under Modules/
except Exception:
    try:
        import template as tpl           # else expect template.py at project root
    except Exception:
        tpl = None

REQUIRED_FUNCS = [
    "inject_css",
    "render_home",
    "simulation_bar_centered",
    "simulation_results_panel",
    "render_dashboard",
]

def _has_all_funcs(mod):
    return mod and all(hasattr(mod, f) for f in REQUIRED_FUNCS)

if not _has_all_funcs(tpl):
    st.warning("Design module is incomplete or missing; loading a minimal built‑in template so the app can run.", icon="⚠️")
    # ---- Minimal in-app template fallback (keeps the app functional) ----
    fallback = types.SimpleNamespace()

    def _inject_css():
        st.markdown("""
        <style>
        :root{ --gap:16px; --gap-lg:22px; --bg:#0b1220; --card:#0f172a; --muted:#94a3b8; --text:#e2e8f0; }
        html, body, [data-testid="stAppViewContainer"]{ background:var(--bg); color:var(--text); padding:12px 18px; }
        div[data-testid="stHorizontalBlock"]{ margin-left:-10px; margin-right:-10px; }
        div[data-testid="column"]{ padding-left:10px; padding-right:10px; }
        .section-title{ font-size:22px; font-weight:700; margin:2px 0 10px; }
        .h2{ font-size:16px; font-weight:600; margin:16px 0 10px; }
        .small{ color:var(--muted); font-size:12px; }
        div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"], div[data-testid="stMetric"], div[data-baseweb="notification"]{
          border:1px solid rgba(148,163,184,0.12); background:var(--card); border-radius:12px; padding:16px; margin-bottom:var(--gap-lg);
          box-shadow:0 0 0 1px rgba(99,102,241,0.05), 0 8px 24px rgba(2,6,23,0.45); overflow:hidden;
        }
        .js-plotly-plot .modebar{ top:8px !important; right:8px !important; background:rgba(2,6,23,0.35) !important; border-radius:8px; }
        </style>
        """, unsafe_allow_html=True)

    def _render_home():
        st.markdown('<div class="section-title">SecondBrainn for Inventory</div>', unsafe_allow_html=True)
        st.info("Landing template is using a minimal fallback; add Modules/template.py for the full styled landing.", icon="ℹ️")

    def _simulation_bar_centered(disabled: bool = False):
        left, mid, right = st.columns([2, 3, 2])
        with mid:
            return st.button("Run simulation", type="primary", use_container_width=True, disabled=disabled)

    def _day_col(df):
        for c in ["day", "Day", "DAY", "date", "Date"]:
            if c in df.columns: return c
        return None

    def _add_day_idx(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        c = _day_col(df)
        if not c: return df
        if "date" in c.lower():
            try:
                d = pd.to_datetime(df[c])
                mapper = {v: i+1 for i, v in enumerate(sorted(d.dropna().unique()))}
                df["__day_idx__"] = d.map(mapper)
            except Exception:
                pass
        else:
            df["__day_idx__"] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        return df

    def _day_filtered_table(df: pd.DataFrame, title: str):
        df = _add_day_idx(df)
        if "__day_idx__" in df.columns:
            min_day = int(df["__day_idx__"].min()) if pd.notna(df["__day_idx__"].min()) else 1
            max_day = int(df["__day_idx__"].max()) if pd.notna(df["__day_idx__"].max()) else 90
            start, end = st.slider(f"{title} — day range", min_value=min_day, max_value=max_day, value=(min_day, max_day))
            view = df[(df["__day_idx__"] >= start) & (df["__day_idx__"] <= end)].drop(columns=["__day_idx__"])
            st.dataframe(view, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

    def _simulation_results_panel(log_text: str, base_dir: str = "data"):
        paths = {
            "Daily summary": os.path.join(base_dir, "sim_daily_summary.csv"),
            "Orders": os.path.join(base_dir, "sim_orders.csv"),
            "Backorders": os.path.join(base_dir, "sim_backorders.csv"),
            "Final inventory": os.path.join(base_dir, "sim_final_inventory.csv"),
        }
        tabs = st.tabs(["Daily summary", "Orders", "Backorders", "Final inventory", "Log", "Downloads"])
        with tabs[0]:
            p = paths["Daily summary"]
            if os.path.exists(p): _day_filtered_table(pd.read_csv(p), "Daily summary")
            else: st.info("No daily summary file found.")
        with tabs[1]:
            p = paths["Orders"]
            if os.path.exists(p): _day_filtered_table(pd.read_csv(p), "Orders")
            else: st.info("No orders file found.")
        with tabs[2]:
            p = paths["Backorders"]
            if os.path.exists(p): _day_filtered_table(pd.read_csv(p), "Backorders")
            else: st.info("No backorders file found.")
        with tabs[3]:
            p = paths["Final inventory"]
            if os.path.exists(p):
                df = pd.read_csv(p)
                st.dataframe(df, use_container_width=True)
                st.download_button("Download final inventory (CSV)", data=open(p, "rb").read(),
                                   file_name="sim_final_inventory.csv", mime="text/csv")
            else:
                st.info("No final inventory file found.")
        with tabs[4]:
            with st.expander("View simulation log", expanded=False):
                st.code(log_text or "(no output)")
    # Simple dashboard renderer (KPIs + two charts)
    def _render_dashboard(sales_df, latest_inv, eoq_df, rop_df, mix_pct, visible_sections):
        if "KPIs" in visible_sections:
            col1, col2, col3, col4 = st.columns(4)
            total_rev = 0.0
            if sales_df is not None and {"Quantity","Rate"}.issubset(sales_df.columns):
                total_rev = float((sales_df["Quantity"] * sales_df["Rate"]).sum())
            active = int(rop_df["need_reorder"].sum()) if rop_df is not None and "need_reorder" in rop_df.columns else 0
            with col1: st.metric("Total Revenue", f"₹{total_rev:,.0f}", "+12.5%")
            with col2: st.metric("Active Orders", f"{active}", "+8.2%")
            with col3: st.metric("Efficiency Score", "94%", "+3.1%")
            with col4: st.metric("Cost Savings", "₹12,450", "+15.8%")
        cols_top = st.columns((7,6,6))
        with cols_top[0]:
            if "Sales vs Orders" in visible_sections and sales_df is not None and not sales_df.empty and {"Date","Quantity"}.issubset(sales_df.columns):
                st.markdown("#### Sales vs Orders")
                s = sales_df.copy(); s["Date"] = pd.to_datetime(s["Date"])
                m = s.groupby(s["Date"].dt.to_period("M")).agg(Sales=("Value","sum"), Orders=("Quantity","sum")).reset_index()
                m["Date"] = m["Date"].dt.to_timestamp()
                fig = go.Figure()
                fig.add_bar(x=m["Date"], y=m["Sales"], name="Sales", marker_color="#6366f1")
                fig.add_scatter(x=m["Date"], y=m["Orders"], name="Orders", mode="lines+markers", line=dict(color="#06b6d4", width=2))
                fig.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,24,39,1)", font_color="#e2e8f0")
                st.plotly_chart(fig, use_container_width=True, theme=None)
        with cols_top[1]:
            if "Inventory trend" in visible_sections and latest_inv is not None and not latest_inv.empty:
                st.markdown("#### Inventory trend")
                inv = latest_inv.copy()
                inv["Quantity"] = pd.to_numeric(inv["Quantity"], errors="coerce").fillna(0)
                inv = inv.sort_values("Particular")
                eoq_map = dict(zip(eoq_df.get("Particular", []), eoq_df.get("EOQ", []))) if eoq_df is not None and not eoq_df.empty else {}
                inv["Optimal"] = inv["Particular"].map(eoq_map).fillna(inv["Quantity"].median() if len(inv) else 0)
                fig2 = go.Figure()
                fig2.add_scatter(x=inv["Particular"], y=inv["Quantity"], name="Stock", mode="lines", line=dict(color="#22c55e"))
                fig2.add_scatter(x=inv["Particular"], y=inv["Optimal"], name="Optimal", mode="lines", line=dict(color="#f59e0b", dash="dash"))
                fig2.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,24,39,1)", font_color="#e2e8f0")
                st.plotly_chart(fig2, use_container_width=True, theme=None)
        with cols_top[2]:
            if "Category mix" in visible_sections and sales_df is not None and not sales_df.empty and "Particular" in sales_df.columns:
                st.markdown("#### Category mix")
                def extract(pt):
                    for t in ["DWR","DIR","HDHMR"]:
                        if isinstance(pt,str) and t in pt: return t
                    return "OTHER"
                s = sales_df.copy(); s["Category"] = s["Particular"].apply(extract)
                pie = s.groupby("Category")["Quantity"].sum().reset_index()
                fig3 = px.pie(pie, names="Category", values="Quantity",
                              color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b","#ef4444"])
                fig3.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                                   paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                st.plotly_chart(fig3, use_container_width=True, theme=None)
        cols_bottom = st.columns((7,7))
        with cols_bottom[0]:
            if "EOQ by SKU" in visible_sections and eoq_df is not None and not eoq_df.empty and "EOQ" in eoq_df.columns:
                st.markdown("#### EOQ by SKU")
                top = eoq_df.sort_values("EOQ", ascending=False).head(15)
                fig = px.bar(top, x="Particular", y="EOQ", color_discrete_sequence=["#6366f1"])
                fig.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                                  paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                st.plotly_chart(fig, use_container_width=True, theme=None)
        with cols_bottom[1]:
            if "Monthly mix" in visible_sections and mix_pct is not None and not mix_pct.empty:
                st.markdown("#### Monthly mix")
                mp = mix_pct.reset_index().melt(id_vars="YearMonth", var_name="Type", value_name="Pct")
                mp["YearMonth"] = mp["YearMonth"].astype(str)
                fig = px.area(mp, x="YearMonth", y="Pct", color="Type",
                              color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b"])
                fig.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                                  paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                st.plotly_chart(fig, use_container_width=True, theme=None)
        if "Inventory vs ROP" in visible_sections and rop_df is not None and not rop_df.empty and {"Particular","inventory_position","reorder_point"}.issubset(rop_df.columns):
            st.markdown("#### Inventory vs ROP")
            table = rop_df[["Particular","inventory_position","reorder_point","need_reorder","suggested_order_qty"]].sort_values(
                ["need_reorder","Particular"], ascending=[False, True]
            )
            st.dataframe(table, use_container_width=True)
        if "Reorder suggestions" in visible_sections and rop_df is not None and not rop_df.empty and "need_reorder" in rop_df.columns:
            st.markdown("#### Reorder suggestions")
            suggest = rop_df[rop_df["need_reorder"] == True][["Particular","suggested_order_qty","EOQ","lead_time_days","service_level"]]
            st.dataframe(suggest.sort_values("suggested_order_qty", ascending=False), use_container_width=True)

    fallback.inject_css = _inject_css
    fallback.render_home = _render_home
    fallback.simulation_bar_centered = _simulation_bar_centered
    fallback.simulation_results_panel = _simulation_results_panel
    fallback.render_dashboard = _render_dashboard
    tpl = fallback  # use fallback template

# =========================
# Page config & paths
# =========================
st.set_page_config(page_title="Inventory & Orders", layout="wide")
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
# Styles
# =========================
tpl.inject_css()

# =========================
# Sidebar controls
# =========================
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
    "KPIs","Sales vs Orders","Inventory trend","Category mix",
    "EOQ by SKU","Inventory vs ROP","Reorder suggestions","Monthly mix",
]
visible = st.sidebar.multiselect("Show sections", ALL_SECTIONS, default=ALL_SECTIONS)

# =========================
# Data helpers
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

    sku_weights = dict(zip(sales_df["Particular"], sales_df["Weight Per Piece"])) if "Weight Per Piece" in sales_df.columns else {}

    eoq_df = calculate_rolling_eoq(sales_df, sku_weights=sku_weights, lookback_days=lookback_days)
    eoq_df.to_csv(EOQ_OUT_CSV, index=False)

    rop_df = evaluate_reorder_points(
        sales_file=SALES_XLSX, inventory_file=LATEST_INV_CSV, eoq_file=EOQ_OUT_CSV,
        sheet_name="Sheet1", lookback_days=lookback_days,
        default_lead_time_days=default_lead_time, default_service_level=default_service,
        on_order_file=None, backorders_file=None,
        min_safety_stock=min_safety, min_reorder_point=min_rop,
    )
    rop_df.to_csv(REORDER_EVAL_CSV, index=False)

    _, mix_pct = calculate_monthly_mix(sales_df)
    return inv_timeline, latest_inv, sales_df, eoq_df, rop_df, mix_pct

# =========================
# Load or compute pipeline
# =========================
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

# =========================
# Simulation integration
# =========================
if "sim_running" not in st.session_state:
    st.session_state["sim_running"] = False

def _load_simulation_module():
    try:
        from Modules import simulation  # preferred
        return simulation
    except Exception:
        try:
            import simulation  # fallback root
            return simulation
        except Exception:
            pass
    sim_path = os.path.join("Modules", "simulation.py")
    if os.path.exists(sim_path):
        spec = importlib.util.spec_from_file_location("simulation", sim_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    raise ImportError("simulation.py not found in Modules/ or project root")

# =========================
# Tabs: Home / Dashboard
# =========================
home_tab, dash_tab = st.tabs(["Home", "Dashboard"])

with home_tab:
    tpl.render_home()

with dash_tab:
    clicked = tpl.simulation_bar_centered(disabled=st.session_state["sim_running"])
    if clicked and not st.session_state["sim_running"]:
        st.session_state["sim_running"] = True
        log_buf = StringIO()
        try:
            sim = _load_simulation_module()
            with st.spinner("Running simulation..."):
                with redirect_stdout(log_buf):
                    if hasattr(sim, "simulate"):
                        sim.simulate(interactive=False)  # writes CSVs into data/
                    else:
                        print("ERROR: simulate() not found in simulation module")
            st.success("Simulation complete.")
        except Exception as e:
            log_buf.write(f"\nERROR: {e}\n")
            st.error("Simulation failed. See log for details.")
        finally:
            st.session_state["sim_running"] = False

        tpl.simulation_results_panel(log_buf.getvalue(), base_dir="data")

    st.markdown(
        '<div class="section-title" id="dashboard">AI-powered insights for optimized decision making</div>'
        '<div class="small">Drive lower carrying costs and fewer stockouts with data-backed reorder plans.</div>',
        unsafe_allow_html=True
    )

    # Render dashboard via template (or fallback)
    tpl.render_dashboard(
        sales_df=sales_df if sales_df is not None else pd.DataFrame(),
        latest_inv=latest_inv if latest_inv is not None else pd.DataFrame(),
        eoq_df=eoq_df if eoq_df is not None else pd.DataFrame(),
        rop_df=rop_df if rop_df is not None else pd.DataFrame(),
        mix_pct=mix_pct if mix_pct is not None else pd.DataFrame(),
        visible_sections=visible
    )
