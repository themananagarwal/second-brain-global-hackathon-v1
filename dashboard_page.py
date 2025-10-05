# dashboard_page.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
from contextlib import redirect_stdout
import importlib.util
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def render_dashboard_page(sales_df, latest_inv, eoq_df, rop_df, mix_pct):
    """Main dashboard rendering function with proper data validation"""

    # Dashboard Header
    st.markdown("""
    <div class="page-header" style="background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); 
                                   padding: 2rem; border-radius: 1rem; margin-bottom: 2rem;">
        <h1 class="page-title" style="margin-bottom: 0.5rem;">Business Dashboard</h1>
        <p class="page-subtitle">Real-time insights powered by your business data</p>
    </div>
    """, unsafe_allow_html=True)

    # Data status indicator
    last_update = st.session_state.get("last_compute_time")
    if last_update:
        st.caption(f"📅 Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")

    # Simulation Section
    render_simulation_section()

    # KPIs Section
    render_kpi_cards(sales_df, latest_inv, eoq_df, rop_df)

    # Charts Section
    render_charts_section(sales_df, latest_inv, eoq_df, rop_df, mix_pct)

    # Product Recommendations (based on real data)
    if rop_df is not None and not rop_df.empty:
        render_real_recommendations(rop_df, latest_inv, eoq_df)


def render_simulation_section():
    """Render the simulation control section"""
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">📈 Inventory Simulation</h3>
            <p class="card-subtitle">Simulate future inventory scenarios based on demand patterns and ordering policies.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Simulation parameters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sim_days = st.number_input("Simulation Days", min_value=30, max_value=365, value=90, step=30)
    with col2:
        lead_time = st.number_input("Lead Time (days)", min_value=1, max_value=30, value=7, step=1)
    with col3:
        service_level = st.slider("Service Level", min_value=0.80, max_value=0.99, value=0.95, step=0.01, format="%.2f")
    with col4:
        st.write("")  # Spacing
        st.write("")
        run_sim = st.button("🚀 Run Simulation", use_container_width=True, type="primary")

    if run_sim:
        run_simulation(sim_days, lead_time, service_level)


def render_kpi_cards(sales_df, latest_inv, eoq_df, rop_df):
    """Render KPI metric cards with REAL calculated data"""

    # Calculate real metrics
    total_rev = 0.0
    total_quantity = 0
    avg_order_value = 0.0

    if sales_df is not None and not sales_df.empty:
        if "Quantity" in sales_df.columns and "Rate" in sales_df.columns:
            # Calculate total revenue
            sales_df_copy = sales_df.copy()
            sales_df_copy["Value"] = pd.to_numeric(sales_df_copy.get("Quantity", 0), errors="coerce") * pd.to_numeric(sales_df_copy.get("Rate", 0), errors="coerce")
            total_rev = float(sales_df_copy["Value"].sum())
            total_quantity = int(pd.to_numeric(sales_df["Quantity"], errors="coerce").sum())

            if total_quantity > 0:
                avg_order_value = total_rev / len(sales_df)

    # Items needing reorder
    items_to_reorder = 0
    if rop_df is not None and not rop_df.empty and "need_reorder" in rop_df.columns:
        items_to_reorder = int(rop_df["need_reorder"].sum())

    # Total SKUs in inventory
    total_skus = 0
    total_inventory_value = 0.0
    if latest_inv is not None and not latest_inv.empty:
        total_skus = len(latest_inv)
        if "Quantity" in latest_inv.columns and "Rate" in latest_inv.columns:
            latest_inv_calc = latest_inv.copy()
            latest_inv_calc["Value"] = pd.to_numeric(latest_inv_calc.get("Quantity", 0), errors="coerce") * pd.to_numeric(latest_inv_calc.get("Rate", 0), errors="coerce")
            total_inventory_value = float(latest_inv_calc["Value"].sum())

    # Stock coverage (average days of stock)
    stock_coverage_days = 0
    if rop_df is not None and not rop_df.empty and "daily_demand_mean" in rop_df.columns:
        valid_demand = rop_df[rop_df["daily_demand_mean"] > 0].copy()
        if not valid_demand.empty and latest_inv is not None:
            # Merge with inventory
            coverage_df = valid_demand.merge(
                latest_inv[["Particular", "Quantity"]],
                on="Particular",
                how="left"
            )
            coverage_df["days_coverage"] = pd.to_numeric(coverage_df["Quantity"], errors="coerce") / coverage_df["daily_demand_mean"]
            stock_coverage_days = int(coverage_df["days_coverage"].mean())

    # Render KPI cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💰 Total Revenue</div>
            <div class="metric-value">₹{total_rev:,.0f}</div>
            <div class="metric-change neutral">{total_quantity:,} units sold</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        status_class = "negative" if items_to_reorder > 0 else "positive"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📋 Items to Reorder</div>
            <div class="metric-value">{items_to_reorder}</div>
            <div class="metric-change {status_class}">out of {total_skus} SKUs</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        coverage_class = "negative" if stock_coverage_days < 14 else "positive" if stock_coverage_days > 30 else "neutral"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">⏱️ Avg Stock Coverage</div>
            <div class="metric-value">{stock_coverage_days} days</div>
            <div class="metric-change {coverage_class}">current inventory</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💼 Inventory Value</div>
            <div class="metric-value">₹{total_inventory_value:,.0f}</div>
            <div class="metric-change neutral">{total_skus} active SKUs</div>
        </div>
        """, unsafe_allow_html=True)


def render_charts_section(sales_df, latest_inv, eoq_df, rop_df, mix_pct):
    """Render charts and visualizations with proper data validation"""

    # First row of charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card"><h3 class="card-title">📈 Sales Trend</h3>', unsafe_allow_html=True)
        if sales_df is not None and not sales_df.empty and {"Date", "Quantity"}.issubset(sales_df.columns):
            render_sales_trend_chart(sales_df)
        else:
            st.info("📊 Sales data not available. Please ensure sales data is loaded correctly.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><h3 class="card-title">📦 Inventory vs Optimal Levels</h3>',
                    unsafe_allow_html=True)
        if latest_inv is not None and not latest_inv.empty:
            render_inventory_chart(latest_inv, eoq_df)
        else:
            st.info("📈 Inventory data not available. Please rebuild to generate data.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Second row - Product mix and reorder analysis
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card"><h3 class="card-title">📊 Product Mix Analysis</h3>', unsafe_allow_html=True)
        if mix_pct is not None and not mix_pct.empty:
            render_product_mix_chart(mix_pct)
        else:
            st.info("📊 Product mix data not available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><h3 class="card-title">⚠️ Reorder Status</h3>', unsafe_allow_html=True)
        if rop_df is not None and not rop_df.empty:
            render_reorder_status_chart(rop_df)
        else:
            st.info("📊 Reorder data not available.")
        st.markdown('</div>', unsafe_allow_html=True)


def render_sales_trend_chart(sales_df):
    """Render sales trend chart with proper validation"""
    try:
        s = sales_df.copy()
        s["Date"] = pd.to_datetime(s["Date"], errors="coerce")
        s = s.dropna(subset=["Date"])

        if s.empty:
            st.warning("No valid date data available for trend analysis.")
            return

        # Ensure we have Quantity
        if "Quantity" not in s.columns:
            st.warning("Sales data missing Quantity column.")
            return

        s["Quantity"] = pd.to_numeric(s["Quantity"], errors="coerce").fillna(0)

        # Calculate Value if Rate exists, otherwise use Quantity
        if "Rate" in s.columns:
            s["Rate"] = pd.to_numeric(s["Rate"], errors="coerce").fillna(0)
            s["Value"] = s["Quantity"] * s["Rate"]
        else:
            s["Value"] = s["Quantity"]

        # Create monthly aggregation
        monthly = s.groupby(s["Date"].dt.to_period("M")).agg({
            "Value": "sum",
            "Quantity": "sum"
        }).reset_index()

        if monthly.empty:
            st.warning("Insufficient data for trend chart.")
            return

        monthly["Date"] = monthly["Date"].dt.to_timestamp()

        # Create the chart
        fig = go.Figure()

        # Add area chart for sales value
        fig.add_scatter(
            x=monthly["Date"],
            y=monthly["Value"],
            mode='lines',
            name='Sales Value',
            fill='tozeroy',
            fillcolor='rgba(14, 165, 233, 0.1)',
            line=dict(color='#0ea5e9', width=3)
        )

        # Add line for quantity
        fig.add_scatter(
            x=monthly["Date"],
            y=monthly["Quantity"],
            mode='lines+markers',
            name='Quantity',
            line=dict(color='#06b6d4', width=2),
            marker=dict(size=6, color='#06b6d4'),
            yaxis="y2"
        )

        fig.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#374151"),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(title="Sales Value (₹)", side="left"),
            yaxis2=dict(title="Quantity", side="right", overlaying="y")
        )

        fig.update_xaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)')
        fig.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)')

        st.plotly_chart(fig, use_container_width=True, theme=None)

    except Exception as e:
        logger.error(f"Error rendering sales trend chart: {str(e)}")
        st.error(f"Unable to render sales trend: {str(e)}")


def render_inventory_chart(latest_inv, eoq_df):
    """Render inventory vs optimal levels chart with pagination"""
    try:
        inv = latest_inv.copy()
        inv["Quantity"] = pd.to_numeric(inv["Quantity"], errors="coerce").fillna(0)
        inv = inv.sort_values("Quantity", ascending=False)

        # Pagination controls
        items_per_page = 10
        total_items = len(inv)
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

        page = st.selectbox("Select page", range(1, total_pages + 1), key="inv_chart_page")
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)

        inv_page = inv.iloc[start_idx:end_idx]

        # Map EOQ values
        eoq_map = {}
        if eoq_df is not None and not eoq_df.empty and "Particular" in eoq_df.columns and "EOQ" in eoq_df.columns:
            eoq_map = dict(zip(eoq_df["Particular"], eoq_df["EOQ"]))

        inv_page["Optimal"] = inv_page["Particular"].map(eoq_map)

        # Fill missing optimal values with median of available EOQs or current quantity
        if inv_page["Optimal"].isna().any():
            fill_value = eoq_df["EOQ"].median() if eoq_df is not None and not eoq_df.empty else inv_page["Quantity"].median()
            inv_page["Optimal"] = inv_page["Optimal"].fillna(fill_value)

        fig = go.Figure()

        # Add current inventory bars
        fig.add_bar(
            x=inv_page["Particular"],
            y=inv_page["Quantity"],
            name='Current Stock',
            marker_color='#0ea5e9',
            opacity=0.8,
            text=inv_page["Quantity"].round(0),
            textposition='outside'
        )

        # Add optimal level bars
        fig.add_bar(
            x=inv_page["Particular"],
            y=inv_page["Optimal"],
            name='Optimal EOQ',
            marker_color='#22c55e',
            opacity=0.6,
            text=inv_page["Optimal"].round(0),
            textposition='outside'
        )

        fig.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=30, b=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#374151"),
            barmode='group',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig.update_xaxes(
            showgrid=False,
            tickangle=45,
            tickmode='linear'
        )
        fig.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)')

        st.plotly_chart(fig, use_container_width=True, theme=None)

        st.caption(f"Showing items {start_idx + 1}-{end_idx} of {total_items}")

    except Exception as e:
        logger.error(f"Error rendering inventory chart: {str(e)}")
        st.error(f"Unable to render inventory chart: {str(e)}")


def render_product_mix_chart(mix_pct):
    """Render actual product mix from data"""
    try:
        if mix_pct is None or mix_pct.empty:
            st.info("No product mix data available")
            return

        # Take top 10 products by percentage
        top_products = mix_pct.head(10)

        fig = px.pie(
            top_products,
            names=top_products.index,
            values='pct',
            title='',
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}<br>%{percent}<extra></extra>'
        )

        fig.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#374151"),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )

        st.plotly_chart(fig, use_container_width=True, theme=None)

    except Exception as e:
        logger.error(f"Error rendering product mix: {str(e)}")
        st.error(f"Unable to render product mix: {str(e)}")


def render_reorder_status_chart(rop_df):
    """Render reorder status visualization"""
    try:
        if "need_reorder" not in rop_df.columns:
            st.warning("Reorder status not available in data")
            return

        # Count items by reorder status
        reorder_counts = rop_df["need_reorder"].value_counts()

        labels = ["Needs Reorder" if idx else "Stock OK" for idx in reorder_counts.index]
        values = reorder_counts.values
        colors = ['#ef4444' if "Needs" in label else '#22c55e' for label in labels]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
            textinfo='value+percent',
            hovertemplate='%{label}<br>%{value} items<br>%{percent}<extra></extra>'
        )])

        fig.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#374151"),
            showlegend=True,
            annotations=[dict(
                text=f'{reorder_counts.sum()}<br>Total SKUs',
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )]
        )

        st.plotly_chart(fig, use_container_width=True, theme=None)

        # Show items needing reorder
        items_to_reorder = rop_df[rop_df["need_reorder"] == True]
        if not items_to_reorder.empty:
            with st.expander(f"📋 View {len(items_to_reorder)} items needing reorder"):
                display_cols = ["Particular", "current_inventory", "reorder_point", "suggested_order_qty"]
                available_cols = [col for col in display_cols if col in items_to_reorder.columns]
                st.dataframe(
                    items_to_reorder[available_cols].sort_values("reorder_point", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )

    except Exception as e:
        logger.error(f"Error rendering reorder status: {str(e)}")
        st.error(f"Unable to render reorder status: {str(e)}")


def render_real_recommendations(rop_df, latest_inv, eoq_df):
    """Render recommendations based on actual data analysis"""

    st.markdown("""
    <div class="card">
        <h3 class="card-title">💡 Intelligent Recommendations</h3>
        <p class="card-subtitle">Based on your current inventory and demand patterns</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Items urgently needing reorder
        if "need_reorder" in rop_df.columns:
            urgent_items = rop_df[rop_df["need_reorder"] == True].copy()

            if not urgent_items.empty:
                # Calculate urgency score
                if "current_inventory" in urgent_items.columns and "daily_demand_mean" in urgent_items.columns:
                    urgent_items["days_left"] = (
                        pd.to_numeric(urgent_items["current_inventory"], errors="coerce") /
                        pd.to_numeric(urgent_items["daily_demand_mean"], errors="coerce").replace(0, 1)
                    ).fillna(999)
                    urgent_items = urgent_items.sort_values("days_left")

                st.markdown("#### ⚠️ Priority Reorders")
                top_urgent = urgent_items.head(5)

                for _, row in top_urgent.iterrows():
                    days_left = row.get("days_left", "N/A")
                    days_text = f"{days_left:.0f} days" if isinstance(days_left, (int, float)) and days_left < 999 else "Low stock"
                    order_qty = row.get("suggested_order_qty", row.get("EOQ", "N/A"))

                    st.markdown(f"""
                    <div style="padding: 0.75rem; background: #fef2f2; border-left: 3px solid #ef4444; margin-bottom: 0.5rem; border-radius: 0.5rem;">
                        <div style="font-weight: 600; color: #1f2937;">{row.get('Particular', 'Unknown')}</div>
                        <div style="font-size: 0.875rem; color: #64748b; margin-top: 0.25rem;">
                            Stock: {row.get('current_inventory', 0):.0f} | Order: {order_qty:.0f} units | {days_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ All items are adequately stocked!")

    with col2:
        # Overstocked items
        if latest_inv is not None and eoq_df is not None:
            st.markdown("#### 📦 Overstocked Items")

            merged = latest_inv.merge(eoq_df[["Particular", "EOQ"]], on="Particular", how="left")
            merged["Quantity"] = pd.to_numeric(merged["Quantity"], errors="coerce").fillna(0)
            merged["EOQ"] = pd.to_numeric(merged["EOQ"], errors="coerce")
            merged["excess_pct"] = ((merged["Quantity"] - merged["EOQ"]) / merged["EOQ"]) * 100

            overstocked = merged[merged["excess_pct"] > 50].sort_values("excess_pct", ascending=False).head(5)

            if not overstocked.empty:
                for _, row in overstocked.iterrows():
                    st.markdown(f"""
                    <div style="padding: 0.75rem; background: #fef9c3; border-left: 3px solid #f59e0b; margin-bottom: 0.5rem; border-radius: 0.5rem;">
                        <div style="font-weight: 600; color: #1f2937;">{row.get('Particular', 'Unknown')}</div>
                        <div style="font-size: 0.875rem; color: #64748b; margin-top: 0.25rem;">
                            Current: {row['Quantity']:.0f} | Optimal: {row['EOQ']:.0f} | {row['excess_pct']:.0f}% excess
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No significantly overstocked items!")


def run_simulation(days=90, lead_time=7, service_level=0.95):
    """Run inventory simulation with progress tracking"""
    try:
        with st.spinner(f"Running {days}-day simulation..."):
            # Check if simulation.py exists
            sim_file = "Modules/simulation.py"
            if not os.path.exists(sim_file):
                st.error(f"❌ Simulation module not found: {sim_file}")
                return

            # Load simulation module
            spec = importlib.util.spec_from_file_location("simulation", sim_file)
            if spec is None or spec.loader is None:
                st.error("❌ Failed to load simulation module")
                return

            sim_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sim_module)

            # Run simulation
            logger.info(f"Starting simulation: {days} days, lead_time={lead_time}, service_level={service_level}")

            # Capture output
            log_buf = StringIO()
            with redirect_stdout(log_buf):
                if hasattr(sim_module, 'main'):
                    sim_module.main()
                else:
                    st.error("❌ Simulation module missing 'main' function")
                    return

            st.success(f"✅ Simulation completed successfully!")
            logger.info("Simulation completed")

            # Show results
            render_simulation_results(log_buf.getvalue())

    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        st.error(f"❌ Simulation failed: {str(e)}")
        st.info("Please check the simulation module and data files.")


def render_simulation_results(log_text):
    """Render simulation results in tabs"""
    st.markdown("### 📊 Simulation Results")

    tab1, tab2, tab3, tab4 = st.tabs(["📈 Daily Summary", "📋 Orders", "⚠️ Backorders", "📊 Final Inventory"])

    with tab1:
        render_simulation_table("data/sim_daily_summary.csv", "Daily Summary")

    with tab2:
        render_simulation_table("data/sim_orders.csv", "Orders")

    with tab3:
        render_simulation_table("data/sim_backorders.csv", "Backorders")

    with tab4:
        render_simulation_table("data/sim_final_inventory.csv", "Final Inventory", show_download=True)


def render_simulation_table(file_path, title, show_download=False):
    """Render simulation data table with improved day filtering"""
    if not os.path.exists(file_path):
        st.info(f"📄 No {title.lower()} data available yet. Run simulation to generate results.")
        return

    try:
        df = pd.read_csv(file_path)

        if df.empty:
            st.info(f"📄 No data in {title.lower()} file.")
            return

        # Add day filter if day column exists
        day_col = None
        for col in ["day", "Day", "DAY"]:
            if col in df.columns:
                day_col = col
                break

        if day_col:
            days = pd.to_numeric(df[day_col], errors="coerce").dropna()
            if not days.empty:
                min_day, max_day = int(days.min()), int(days.max())

                col1, col2 = st.columns([3, 1])
                with col1:
                    day_range = st.slider(
                        f"Filter by day",
                        min_value=min_day,
                        max_value=max_day,
                        value=(min_day, min(min_day + 29, max_day)),
                        key=f"slider_{title}"
                    )

                with col2:
                    st.metric("Days Selected", day_range[1] - day_range[0] + 1)

                filtered_df = df[
                    (pd.to_numeric(df[day_col], errors="coerce") >= day_range[0]) &
                    (pd.to_numeric(df[day_col], errors="coerce") <= day_range[1])
                ]
            else:
                filtered_df = df
        else:
            filtered_df = df

        # Display dataframe
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        # Download button
        if show_download:
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                f"📥 Download {title}",
                data=csv_data,
                file_name=f"filtered_{os.path.basename(file_path)}",
                mime="text/csv",
                key=f"download_{title}"
            )

    except Exception as e:
        logger.error(f"Error rendering simulation table {file_path}: {str(e)}")
        st.error(f"Error loading {title}: {str(e)}")
