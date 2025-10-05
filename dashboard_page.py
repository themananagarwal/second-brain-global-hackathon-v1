# dashboard_page.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
from contextlib import redirect_stdout
import importlib.util
import os


def render_dashboard_page(sales_df, latest_inv, eoq_df, rop_df, mix_pct):
    # Dashboard Header
    st.markdown("""
    <div class="page-header" style="background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); 
                                   padding: 2rem; border-radius: 1rem; margin-bottom: 2rem;">
        <h1 class="page-title" style="margin-bottom: 0.5rem;">Business Dashboard</h1>
        <p class="page-subtitle">AI-powered insights for optimized decision making</p>
    </div>
    """, unsafe_allow_html=True)

    # Simulation Section
    render_simulation_section()

    # KPIs Section
    render_kpi_cards(sales_df, rop_df)

    # Charts Section
    render_charts_section(sales_df, latest_inv, eoq_df, rop_df, mix_pct)

    # AI Recommendations
    render_ai_recommendations(rop_df)


def render_simulation_section():
    """Render the simulation control section"""
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">📈 AI-Powered Next Order Suggestion</h3>
            <p class="card-subtitle">Based on historical demand patterns, seasonal trends, and current inventory levels, our AI recommends the following optimized order reducing carrying costs by 18%.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Simulation Button (Centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Run AI Simulation", use_container_width=True, type="primary"):
            run_simulation()


def render_kpi_cards(sales_df, rop_df):
    """Render KPI metric cards"""
    # Calculate metrics
    total_rev = 0.0
    if sales_df is not None and {"Quantity", "Rate"}.issubset(sales_df.columns):
        total_rev = float((sales_df["Quantity"] * sales_df["Rate"]).sum())

    active = int(rop_df["need_reorder"].sum()) if rop_df is not None and "need_reorder" in rop_df.columns else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">💰 Total Revenue</div>
            <div class="metric-value">₹{:,.0f}</div>
            <div class="metric-change positive">+12.5% <span style="color: #64748b;">from last month</span></div>
        </div>
        """.format(total_rev), unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">📋 Active Orders</div>
            <div class="metric-value">{}</div>
            <div class="metric-change positive">+8.2% <span style="color: #64748b;">processing</span></div>
        </div>
        """.format(active), unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">⚡ Efficiency Score</div>
            <div class="metric-value">94%</div>
            <div class="metric-change positive">+3.1% <span style="color: #64748b;">optimization rate</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">💡 Cost Savings</div>
            <div class="metric-value">₹12,450</div>
            <div class="metric-change positive">+15.8% <span style="color: #64748b;">this quarter</span></div>
        </div>
        """, unsafe_allow_html=True)


def render_charts_section(sales_df, latest_inv, eoq_df, rop_df, mix_pct):
    """Render charts and visualizations"""
    # First row of charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card"><h3 class="card-title">📈 Sales & Orders Trend</h3>', unsafe_allow_html=True)
        if sales_df is not None and not sales_df.empty and {"Date", "Quantity"}.issubset(sales_df.columns):
            render_sales_trend_chart(sales_df)
        else:
            st.info("📊 Sales data not available. Please upload sales data and rebuild.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><h3 class="card-title">📦 Inventory vs Optimal Levels</h3>',
                    unsafe_allow_html=True)
        if latest_inv is not None and not latest_inv.empty:
            render_inventory_chart(latest_inv, eoq_df)
        else:
            st.info("📈 Inventory data not available. Please rebuild to generate data.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Product Combination Recommendation
    if rop_df is not None and not rop_df.empty and "need_reorder" in rop_df.columns:
        render_product_recommendations(rop_df)


def render_sales_trend_chart(sales_df):
    """Render sales trend chart"""
    s = sales_df.copy()
    s["Date"] = pd.to_datetime(s["Date"])

    # Create monthly aggregation
    monthly = s.groupby(s["Date"].dt.to_period("M")).agg(
        Sales=("Value", "sum"),
        Orders=("Quantity", "sum")
    ).reset_index()
    monthly["Date"] = monthly["Date"].dt.to_timestamp()

    # Create the chart
    fig = go.Figure()

    # Add area chart for sales
    fig.add_scatter(
        x=monthly["Date"],
        y=monthly["Sales"],
        mode='lines',
        name='Sales',
        fill='tonexty',
        fillcolor='rgba(14, 165, 233, 0.1)',
        line=dict(color='#0ea5e9', width=3)
    )

    # Add line for orders
    fig.add_scatter(
        x=monthly["Date"],
        y=monthly["Orders"],
        mode='lines+markers',
        name='Orders',
        line=dict(color='#06b6d4', width=2),
        marker=dict(size=8, color='#06b6d4')
    )

    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
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
        )
    )

    fig.update_xaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)')

    st.plotly_chart(fig, use_container_width=True, theme=None)


def render_inventory_chart(latest_inv, eoq_df):
    """Render inventory vs optimal levels chart"""
    inv = latest_inv.copy()
    inv["Quantity"] = pd.to_numeric(inv["Quantity"], errors="coerce").fillna(0)
    inv = inv.sort_values("Particular").head(10)  # Top 10 items

    # Map EOQ values
    eoq_map = dict(
        zip(eoq_df.get("Particular", []), eoq_df.get("EOQ", []))) if eoq_df is not None and not eoq_df.empty else {}
    inv["Optimal"] = inv["Particular"].map(eoq_map).fillna(inv["Quantity"].median() if len(inv) else 0)

    fig = go.Figure()

    # Add current inventory bars
    fig.add_bar(
        x=inv["Particular"],
        y=inv["Quantity"],
        name='Current Stock',
        marker_color='#0ea5e9',
        opacity=0.8
    )

    # Add optimal level bars
    fig.add_bar(
        x=inv["Particular"],
        y=inv["Optimal"],
        name='Optimal Level',
        marker_color='#22c55e',
        opacity=0.8
    )

    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
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

    fig.update_xaxes(showgrid=False, tickangle=45)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)')

    st.plotly_chart(fig, use_container_width=True, theme=None)


def render_product_recommendations(rop_df):
    """Render product combination recommendations"""
    st.markdown("""
    <div class="card" style="background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%); color: white; margin: 2rem 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <h3 style="color: white; margin: 0;">Total Order Cost</h3>
                <div style="font-size: 2rem; font-weight: 700;">$8,450</div>
            </div>
            <div>
                <h3 style="color: white; margin: 0;">Estimated Savings</h3>
                <div style="font-size: 2rem; font-weight: 700; color: #22c55e;">$1,520</div>
            </div>
            <div>
                <h3 style="color: white; margin: 0;">Delivery Timeline</h3>
                <div style="font-size: 2rem; font-weight: 700;">3-5 business days</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Recommended products
    st.markdown("""
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 class="card-title">🎯 Recommended Product Combination</h3>
        </div>
    """, unsafe_allow_html=True)

    # Get reorder suggestions
    suggest = rop_df[rop_df["need_reorder"] == True].head(5) if "need_reorder" in rop_df.columns else pd.DataFrame()

    if not suggest.empty:
        for _, row in suggest.iterrows():
            qty = int(row.get("suggested_order_qty", 0))
            particular = row.get("Particular", "Unknown")
            rate = row.get("Rate", 0)
            total = qty * rate if rate else 0

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; 
                        padding: 1rem; background: #f8fafc; border-radius: 0.5rem; margin-bottom: 0.5rem;">
                <div>
                    <div style="font-weight: 600; color: #374151;">{particular}</div>
                    <div style="color: #64748b; font-size: 0.875rem;">Qty: {qty}</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: #64748b; font-size: 0.875rem;">₹{rate:.0f}/unit</div>
                    <div style="font-weight: 600; color: #0ea5e9;">₹{total:,.0f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Ready to optimize section
    st.markdown("""
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 0.75rem; 
                padding: 1rem; margin: 1rem 0; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="color: #16a34a; font-weight: 600; margin-bottom: 0.25rem;">✅ Ready to optimize your inventory?</div>
            <div style="color: #15803d; font-size: 0.875rem;">This combination maximizes efficiency and minimizes costs</div>
        </div>
        <button style="background: #0ea5e9; color: white; border: none; padding: 0.75rem 1.5rem; 
                       border-radius: 0.5rem; font-weight: 600; cursor: pointer;">
            Approve Order
        </button>
    </div>
    """, unsafe_allow_html=True)


def render_ai_recommendations(rop_df):
    """Render AI recommendations section"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card">
            <h3 class="card-title">📊 Inventory by Category</h3>
            <div style="margin: 1rem 0;">
                <div style="margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Plywood</span><span style="font-weight: 600;">45%</span>
                    </div>
                    <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin-top: 0.25rem;">
                        <div style="background: #0ea5e9; height: 100%; width: 45%; border-radius: 4px;"></div>
                    </div>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Adhesives</span><span style="font-weight: 600;">25%</span>
                    </div>
                    <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin-top: 0.25rem;">
                        <div style="background: #06b6d4; height: 100%; width: 25%; border-radius: 4px;"></div>
                    </div>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Hardware</span><span style="font-weight: 600;">20%</span>
                    </div>
                    <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin-top: 0.25rem;">
                        <div style="background: #22c55e; height: 100%; width: 20%; border-radius: 4px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Tools</span><span style="font-weight: 600;">10%</span>
                    </div>
                    <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin-top: 0.25rem;">
                        <div style="background: #f59e0b; height: 100%; width: 10%; border-radius: 4px;"></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <h3 class="card-title">📈 Inventory Status</h3>
            <div style="margin: 1rem 0;">
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Plywood 18mm</span>
                        <span style="background: #fef2f2; color: #dc2626; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem;">low</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.875rem; margin: 0.25rem 0;">Current: 45 | Optimal: 80</div>
                    <div style="background: #e5e7eb; height: 8px; border-radius: 4px;">
                        <div style="background: #dc2626; height: 100%; width: 15%; border-radius: 4px;"></div>
                    </div>
                </div>

                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Plywood 12mm</span>
                        <span style="background: #dbeafe; color: #2563eb; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem;">optimal</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.875rem; margin: 0.25rem 0;">Current: 100 | Optimal: 100</div>
                    <div style="background: #e5e7eb; height: 8px; border-radius: 4px;">
                        <div style="background: #2563eb; height: 100%; width: 85%; border-radius: 4px;"></div>
                    </div>
                </div>

                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Plywood 6mm</span>
                        <span style="background: #fef9c3; color: #d97706; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem;">high</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.875rem; margin: 0.25rem 0;">Current: 95 | Optimal: 80</div>
                    <div style="background: #e5e7eb; height: 8px; border-radius: 4px;">
                        <div style="background: #d97706; height: 100%; width: 92%; border-radius: 4px;"></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card">
            <h3 class="card-title">🤖 AI Recommendations</h3>
            <div style="margin: 1rem 0;">
                <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: #dc2626; margin-right: 0.5rem;">⚠️</span>
                        <span style="font-weight: 600; color: #dc2626;">Plywood 18mm</span>
                        <span style="background: #dc2626; color: white; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; margin-left: 0.5rem;">high</span>
                    </div>
                    <div style="color: #7f1d1d; font-size: 0.875rem;">Demand spike predicted</div>
                    <div style="font-weight: 600; color: #0ea5e9; margin-top: 0.5rem;">Order 30 units</div>
                    <div style="color: #64748b; font-size: 0.75rem;">in 2 days</div>
                </div>

                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: #16a34a; margin-right: 0.5rem;">⭕</span>
                        <span style="font-weight: 600; color: #15803d;">Adhesive A1</span>
                        <span style="background: #16a34a; color: white; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; margin-left: 0.5rem;">medium</span>
                    </div>
                    <div style="color: #14532d; font-size: 0.875rem;">Regular restocking</div>
                    <div style="font-weight: 600; color: #0ea5e9; margin-top: 0.5rem;">Order 15 units</div>
                    <div style="color: #64748b; font-size: 0.75rem;">in 1 week</div>
                </div>

                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 0.5rem; padding: 1rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: #16a34a; margin-right: 0.5rem;">✅</span>
                        <span style="font-weight: 600; color: #15803d;">Optimization Impact</span>
                    </div>
                    <div style="color: #14532d; font-size: 0.875rem; margin-bottom: 0.5rem;">Following these recommendations will reduce stockouts by 35% and decrease carrying costs by $2,400/month.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def run_simulation():
    """Handle simulation execution"""
    try:
        # Try to import simulation module
        def _load_simulation_module():
            try:
                from Modules import simulation
                return simulation
            except Exception:
                try:
                    import simulation
                    return simulation
                except Exception:
                    pass

            sim_path = os.path.join("Modules", "simulation.py")
            if os.path.exists(sim_path):
                spec = importlib.util.spec_from_file_location("simulation", sim_path)
                mod = importlib.util.module_from_spec(spec)
                assert spec and spec.loader
                spec.loader.exec_module(mod)
                return mod
            raise ImportError("simulation.py not found")

        log_buf = StringIO()
        with st.spinner("🤖 Running AI simulation..."):
            sim = _load_simulation_module()
            with redirect_stdout(log_buf):
                if hasattr(sim, "simulate"):
                    sim.simulate(interactive=False)
                else:
                    print("ERROR: simulate() not found")

        st.success("✅ Simulation complete!")

        # Show results in tabs
        render_simulation_results(log_buf.getvalue())

    except Exception as e:
        st.error(f"❌ Simulation failed: {str(e)}")


def render_simulation_results(log_text):
    """Render simulation results in tabs"""
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
    """Render simulation data table with day filter"""
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)

        # Add day filter if day column exists
        day_col = None
        for col in ["day", "Day", "DAY", "date", "Date"]:
            if col in df.columns:
                day_col = col
                break

        if day_col:
            if "date" in day_col.lower():
                try:
                    dates = pd.to_datetime(df[day_col])
                    unique_dates = sorted(dates.dropna().unique())
                    day_range = st.slider(
                        f"{title} - Select date range",
                        min_value=0,
                        max_value=len(unique_dates) - 1,
                        value=(0, min(29, len(unique_dates) - 1)),
                        format="Day %d"
                    )
                    selected_dates = unique_dates[day_range[0]:day_range[1] + 1]
                    filtered_df = df[dates.isin(selected_dates)]
                except Exception:
                    filtered_df = df
            else:
                days = pd.to_numeric(df[day_col], errors="coerce").dropna()
                if not days.empty:
                    min_day, max_day = int(days.min()), int(days.max())
                    day_range = st.slider(
                        f"{title} - Day range",
                        min_value=min_day,
                        max_value=max_day,
                        value=(min_day, min(min_day + 29, max_day))
                    )
                    filtered_df = df[(pd.to_numeric(df[day_col], errors="coerce") >= day_range[0]) &
                                     (pd.to_numeric(df[day_col], errors="coerce") <= day_range[1])]
                else:
                    filtered_df = df
        else:
            filtered_df = df

        st.dataframe(filtered_df, use_container_width=True)

        if show_download:
            st.download_button(
                f"📥 Download {title}",
                data=open(file_path, "rb").read(),
                file_name=os.path.basename(file_path),
                mime="text/csv"
            )
    else:
        st.info(f"📄 No {title.lower()} data available yet.")
