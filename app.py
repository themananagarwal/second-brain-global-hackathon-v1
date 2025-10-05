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
import logging
from datetime import datetime

from Modules.data_ingestion import load_sales_data
from Modules.inventory_tracker import build_inventory_timeline
from Modules.rolling_eoq import calculate_rolling_eoq
from Modules.reorder_evaluator import evaluate_reorder_points
from Modules.trends_analysis import calculate_monthly_mix
from template import inject_global_css
from home_page import render_home_page
from dashboard_page import render_dashboard_page

# =========================
# Logging Configuration
# =========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
OUTPUT_DIR = "outputs"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

SALES_XLSX = os.path.join(DATA_DIR, "MDF Sales data.xlsx")
PURCHASE_XLSX = os.path.join(DATA_DIR, "MDF purchase data.xlsx")
BASE_INV_XLSX = os.path.join(DATA_DIR, "Inventory Base Data.xlsx")

LATEST_INV_CSV = os.path.join(DATA_DIR, "latest_inventory.csv")
EOQ_OUT_CSV = os.path.join(OUTPUT_DIR, "eoq_results.csv")
REORDER_EVAL_CSV = os.path.join(DATA_DIR, "reorder_evaluation.csv")


# =========================
# Session State Initialization
# =========================
def init_session_state():
    """Initialize all session state variables"""
    if "sim_running" not in st.session_state:
        st.session_state["sim_running"] = False
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Home"
    if "last_compute_time" not in st.session_state:
        st.session_state["last_compute_time"] = None
    if "data_loaded" not in st.session_state:
        st.session_state["data_loaded"] = False
    if "error_log" not in st.session_state:
        st.session_state["error_log"] = []


init_session_state()


# =========================
# File Validation
# =========================
def validate_required_files():
    """Check if all required data files exist"""
    required_files = {
        "Sales Data": SALES_XLSX,
        "Purchase Data": PURCHASE_XLSX,
        "Base Inventory": BASE_INV_XLSX
    }

    missing_files = []
    for name, path in required_files.items():
        if not os.path.exists(path):
            missing_files.append(f"{name} ({path})")
            logger.error(f"Missing required file: {path}")

    return missing_files


# =========================
# Data Helpers
# =========================
@st.cache_data(show_spinner=False, ttl=3600)
def load_sales():
    """Load sales data with error handling"""
    try:
        if not os.path.exists(SALES_XLSX):
            logger.error(f"Sales file not found: {SALES_XLSX}")
            return None

        df = load_sales_data(SALES_XLSX, sheet_name="Sheet1")
        if df is None or df.empty:
            logger.warning("Sales data is empty")
            return None

        # Validate required columns
        required_cols = ["Date", "Particular", "Quantity"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Sales data missing columns: {missing_cols}")
            return None

        logger.info(f"Successfully loaded {len(df)} sales records")
        return df
    except Exception as e:
        logger.error(f"Error loading sales data: {str(e)}")
        st.session_state["error_log"].append(f"Sales load error: {str(e)}")
        return None


def try_read_csv(path, description="data"):
    """Safely read CSV with comprehensive error handling"""
    try:
        if not os.path.exists(path):
            logger.warning(f"{description} file not found: {path}")
            return None

        df = pd.read_csv(path)
        if df.empty:
            logger.warning(f"{description} file is empty: {path}")
            return None

        logger.info(f"Successfully loaded {description} from {path}")
        return df
    except Exception as e:
        logger.error(f"Error reading {description} from {path}: {str(e)}")
        st.session_state["error_log"].append(f"{description} read error: {str(e)}")
        return None


@st.cache_data(show_spinner=False, ttl=3600)
def compute_pipeline():
    """
    Run the complete data pipeline with comprehensive error handling
    Returns: (success: bool, results: dict, error_msg: str)
    """
    results = {
        "latest_inv": None,
        "eoq_df": None,
        "rop_df": None,
        "mix_pct": None
    }

    try:
        # Validate files exist
        missing_files = validate_required_files()
        if missing_files:
            error_msg = f"Missing required files: {', '.join(missing_files)}"
            logger.error(error_msg)
            return False, results, error_msg

        logger.info("Starting data pipeline computation...")

        # Step 1: Build inventory timeline
        try:
            logger.info("Building inventory timeline...")
            result = build_inventory_timeline(SALES_XLSX, PURCHASE_XLSX, BASE_INV_XLSX)

            # build_inventory_timeline returns a tuple: (inventory_df, latest_inventory_df)
            if isinstance(result, tuple) and len(result) == 2:
                inventory_timeline, latest_inv_df = result
                results["latest_inv"] = latest_inv_df
            else:
                return False, results, "Inventory timeline returned unexpected format"

            if results["latest_inv"] is None or results["latest_inv"].empty:
                return False, results, "Inventory timeline returned empty results"

            # Save to CSV
            results["latest_inv"].to_csv(LATEST_INV_CSV, index=False)
            logger.info(f"Saved latest inventory with {len(results['latest_inv'])} items")
        except Exception as e:
            return False, results, f"Inventory tracking failed: {str(e)}"

        # Step 2: Calculate EOQ
        try:
            logger.info("Calculating EOQ...")
            sales_df = load_sales()
            if sales_df is None:
                return False, results, "Failed to load sales data for EOQ calculation"

            # Define SKU weights (kg per piece)
            sku_weights = {
                "Plywood 18mm": 25.0,
                "Plywood 12mm": 18.0,
                "Plywood 6mm": 10.0,
                "MDF 18mm": 22.0,
                "MDF 12mm": 15.0
            }

            results["eoq_df"] = calculate_rolling_eoq(
                sales_df,
                sku_weights,
                lookback_days=180
            )

            if results["eoq_df"] is None or results["eoq_df"].empty:
                logger.warning("EOQ calculation returned empty results")
            else:
                results["eoq_df"].to_csv(EOQ_OUT_CSV, index=False)
                logger.info(f"Calculated EOQ for {len(results['eoq_df'])} SKUs")
        except Exception as e:
            logger.error(f"EOQ calculation failed: {str(e)}")
            # Continue with other computations

        # Step 3: Evaluate reorder points
        try:
            logger.info("Evaluating reorder points...")
            results["rop_df"] = evaluate_reorder_points(
                sales_file=SALES_XLSX,
                inventory_file=LATEST_INV_CSV,
                eoq_file=EOQ_OUT_CSV,
                service_level=0.95,
                lead_time_days=7,
                lookback_days=120
            )

            if results["rop_df"] is not None and not results["rop_df"].empty:
                results["rop_df"].to_csv(REORDER_EVAL_CSV, index=False)
                logger.info(f"Evaluated reorder points for {len(results['rop_df'])} SKUs")
        except Exception as e:
            logger.error(f"Reorder evaluation failed: {str(e)}")

        # Step 4: Calculate monthly mix
        try:
            logger.info("Calculating monthly product mix...")
            if sales_df is not None:
                results["mix_pct"] = calculate_monthly_mix(sales_df)
                logger.info("Monthly mix calculation complete")
        except Exception as e:
            logger.error(f"Monthly mix calculation failed: {str(e)}")

        logger.info("Data pipeline completed successfully")
        st.session_state["last_compute_time"] = datetime.now()
        st.session_state["data_loaded"] = True
        return True, results, None

    except Exception as e:
        error_msg = f"Pipeline failed with unexpected error: {str(e)}"
        logger.error(error_msg)
        return False, results, error_msg


# =========================
# Navigation
# =========================
def render_navigation():
    """Render navigation buttons"""
    st.markdown("""
    <div class="nav-container">
        <div class="logo">
            <span style="font-size: 1.5rem; font-weight: 800; color: #0ea5e9;">🧠 SecondBrain</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])

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
# Main App
# =========================
def main():
    """Main application logic"""
    render_navigation()

    # Check for missing files
    missing_files = validate_required_files()
    if missing_files:
        st.error("⚠️ **Missing Required Data Files**")
        st.markdown("The following files are required but not found:")
        for file in missing_files:
            st.markdown(f"- `{file}`")
        st.info("Please ensure all required data files are placed in the `data/` directory.")
        return

    # Route to appropriate page
    if st.session_state["current_page"] == "Home":
        render_home_page()

    elif st.session_state["current_page"] == "Dashboard":
        with st.spinner("Loading dashboard data..."):
            # Load data
            sales_df = load_sales()

            # Compute pipeline if needed
            success, results, error_msg = compute_pipeline()

            if not success:
                st.error(f"❌ **Data Processing Error**")
                st.markdown(f"**Details:** {error_msg}")
                st.info("Please check your data files and try again.")

                # Show error log if available
                if st.session_state["error_log"]:
                    with st.expander("📋 View Error Log"):
                        for error in st.session_state["error_log"]:
                            st.text(error)
                return

            # Render dashboard with computed data
            render_dashboard_page(
                sales_df=sales_df,
                latest_inv=results["latest_inv"],
                eoq_df=results["eoq_df"],
                rop_df=results["rop_df"],
                mix_pct=results["mix_pct"]
            )

    elif st.session_state["current_page"] == "Inventory":
        st.markdown("""
        <div class="page-header" style="background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); 
                                       padding: 2rem; border-radius: 1rem; margin: 2rem;">
            <h1 class="page-title">📦 Inventory Management</h1>
            <p class="page-subtitle">Real-time inventory tracking and optimization</p>
        </div>
        """, unsafe_allow_html=True)

        st.info("🚧 **Under Development** - Advanced inventory management features coming soon!")


if __name__ == "__main__":
    main()
