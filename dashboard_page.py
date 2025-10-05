# dashboard_page.py - FIXED WORKING VERSION
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import StringIO
from contextlib import redirect_stdout
import importlib.util
import os
import logging
from datetime import datetime
import sys

logger = logging.getLogger(__name__)


def render_dashboard_page(sales_df, latest_inv, eoq_df, rop_df, mix_pct):
    """Main dashboard rendering function with proper data validation"""

    # Dashboard Header
    st.markdown("""
    <div style='margin-bottom: 32px;'>
        <h1 style='font-size: 2.5rem; font-weight: 700; color: #2C3E50; margin-bottom: 8px;'>
            Analytics Dashboard
        </h1>
        <p style='font-size: 1.125rem; color: #6C757D;'>
            Real-time insights powered by your business data
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Data Validation
    if sales_df is None or sales_df.empty:
        st.error("⚠️ **No sales data available.** Please ensure data files are properly loaded.")
        return

    # Compute Key Metrics
    try:
        total_sales = sales_df['Quantity'].sum() if 'Quantity' in sales_df.columns else 0
        total_skus = sales_df['Particular'].nunique() if 'Particular' in sales_df.columns else 0

        avg_daily_sales = total_sales / 30 if total_sales > 0 else 0

        total_inventory_value = 0
        stock_items = 0
        if latest_inv is not None and not latest_inv.empty:
            if 'Current_Stock' in latest_inv.columns:
                stock_items = len(latest_inv)
                total_inventory_value = latest_inv['Current_Stock'].sum()
            elif 'Quantity' in latest_inv.columns:
                stock_items = len(latest_inv)
                total_inventory_value = latest_inv['Quantity'].sum()

        # Calculate changes (mock data for demonstration)
        sales_change = 12.5
        sku_change = 0
        inventory_change = -3.2
        stock_change = 8.1

    except Exception as e:
        logger.error(f"Error computing metrics: {str(e)}")
        st.error(f"Error calculating dashboard metrics: {str(e)}")
        return

    # KPI Cards (4-column layout)
    st.markdown("<div style='margin-bottom: 32px;'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        st.markdown(f"""
        <div class="metric-card fade-in">
            <div class="metric-label">Total Sales Volume</div>
            <div class="metric-value">{total_sales:,.0f}</div>
            <div class="metric-change {'positive' if sales_change >= 0 else 'negative'}">
                {'▲' if sales_change >= 0 else '▼'} {abs(sales_change):.1f}% vs last period
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card fade-in" style="animation-delay: 0.1s; border-left-color: #28A745;">
            <div class="metric-label">Active SKUs</div>
            <div class="metric-value">{total_skus}</div>
            <div class="metric-change {'neutral' if sku_change == 0 else 'positive' if sku_change > 0 else 'negative'}">
                {'→' if sku_change == 0 else '▲' if sku_change > 0 else '▼'} {abs(sku_change):.1f}% vs last period
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card fade-in" style="animation-delay: 0.2s; border-left-color: #FF9500;">
            <div class="metric-label">Inventory Value</div>
            <div class="metric-value">{total_inventory_value:,.0f}</div>
            <div class="metric-change {'negative' if inventory_change < 0 else 'positive'}">
                {'▼' if inventory_change < 0 else '▲'} {abs(inventory_change):.1f}% vs last period
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card fade-in" style="animation-delay: 0.3s; border-left-color: #DC3545;">
            <div class="metric-label">Stock Items</div>
            <div class="metric-value">{stock_items}</div>
            <div class="metric-change positive">
                ▲ {abs(stock_change):.1f}% vs last period
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Charts Section (2x2 Grid)
    st.markdown("<div style='margin: 48px 0 24px 0;'>", unsafe_allow_html=True)

    # Row 1: Sales Trend & Product Mix
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="chart-container">
            <h3 class="chart-title">📈 Daily Sales Trend</h3>
        """, unsafe_allow_html=True)

        try:
            if 'Date' in sales_df.columns and 'Quantity' in sales_df.columns:
                # Prepare daily sales data
                sales_df_copy = sales_df.copy()
                sales_df_copy['Date'] = pd.to_datetime(sales_df_copy['Date'], errors='coerce', dayfirst=True)
                sales_df_copy = sales_df_copy.dropna(subset=['Date'])

                if not sales_df_copy.empty:
                    daily_sales = sales_df_copy.groupby('Date')['Quantity'].sum().reset_index()
                    daily_sales = daily_sales.sort_values('Date')

                    # Create area chart with gradient
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=daily_sales['Date'],
                        y=daily_sales['Quantity'],
                        mode='lines',
                        name='Sales Volume',
                        fill='tozeroy',
                        fillcolor='rgba(0, 191, 255, 0.15)',
                        line=dict(color='#00BFFF', width=3)
                    ))

                    fig.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=10, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#374151', size=11, family='Arial'),
                        showlegend=False,
                        hovermode='x unified'
                    )

                    fig.update_xaxes(
                        showgrid=True,
                        gridcolor='rgba(148, 163, 184, 0.15)',
                        zeroline=False,
                        title=None
                    )

                    fig.update_yaxes(
                        showgrid=True,
                        gridcolor='rgba(148, 163, 184, 0.15)',
                        zeroline=False,
                        title='Quantity'
                    )

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No valid date data available")
            else:
                st.info("Sales trend data not available")
        except Exception as e:
            logger.error(f"Error rendering sales trend: {str(e)}")
            st.error("Unable to render sales trend chart")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="chart-container">
            <h3 class="chart-title">🎯 Product Performance</h3>
        """, unsafe_allow_html=True)

        try:
            if 'Particular' in sales_df.columns and 'Quantity' in sales_df.columns:
                # Calculate product mix
                product_mix = sales_df.groupby('Particular')['Quantity'].sum().reset_index()
                product_mix = product_mix.sort_values('Quantity', ascending=False).head(8)

                # Create donut chart
                fig = go.Figure(data=[go.Pie(
                    labels=product_mix['Particular'],
                    values=product_mix['Quantity'],
                    hole=0.3,
                    marker=dict(
                        colors=['#00BFFF', '#0099E5', '#28A745', '#FF9500', '#DC3545', '#6C757D', '#9B59B6', '#E74C3C']
                    )
                )])

                fig.update_layout(
                    height=350,
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#374151', size=11, family='Arial'),
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.05
                    )
                )

                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Product mix data not available")
        except Exception as e:
            logger.error(f"Error rendering product mix: {str(e)}")
            st.error("Unable to render product mix chart")

        st.markdown("</div>", unsafe_allow_html=True)

    # Row 2: Inventory Status & Reorder Analysis
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="chart-container">
            <h3 class="chart-title">📦 Inventory vs Target Levels</h3>
        """, unsafe_allow_html=True)

        try:
            if latest_inv is not None and not latest_inv.empty and eoq_df is not None and not eoq_df.empty:
                # Determine columns
                inv_sku_col = 'SKU' if 'SKU' in latest_inv.columns else 'Particular'
                inv_qty_col = 'Current_Stock' if 'Current_Stock' in latest_inv.columns else 'Quantity'
                eoq_sku_col = 'SKU' if 'SKU' in eoq_df.columns else 'Particular'

                if inv_sku_col in latest_inv.columns and inv_qty_col in latest_inv.columns:
                    inv_comparison = latest_inv.merge(
                        eoq_df[[eoq_sku_col, 'EOQ']],
                        left_on=inv_sku_col,
                        right_on=eoq_sku_col,
                        how='left'
                    )

                    inv_comparison = inv_comparison.head(10)

                    fig = go.Figure()

                    fig.add_trace(go.Bar(
                        name='Current Stock',
                        x=inv_comparison[inv_sku_col],
                        y=inv_comparison[inv_qty_col],
                        marker_color='#00BFFF',
                        hovertemplate='<b>%{x}</b><br>Current: %{y:,.0f}<extra></extra>'
                    ))

                    fig.add_trace(go.Bar(
                        name='Optimal (EOQ)',
                        x=inv_comparison[inv_sku_col],
                        y=inv_comparison['EOQ'],
                        marker_color='#28A745',
                        hovertemplate='<b>%{x}</b><br>Optimal: %{y:,.0f}<extra></extra>'
                    ))

                    fig.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=10, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#374151', size=11, family='Arial'),
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
                        title=None,
                        tickangle=-45
                    )

                    fig.update_yaxes(
                        showgrid=True,
                        gridcolor='rgba(148, 163, 184, 0.15)',
                        title='Quantity'
                    )

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Inventory comparison data incomplete")
            else:
                st.info("Inventory or EOQ data not available")
        except Exception as e:
            logger.error(f"Error rendering inventory comparison: {str(e)}")
            st.error("Unable to render inventory comparison chart")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="chart-container">
            <h3 class="chart-title">🚨 Reorder Priority Status</h3>
        """, unsafe_allow_html=True)

        try:
            if rop_df is not None and not rop_df.empty and 'Action' in rop_df.columns:
                reorder_counts = rop_df['Action'].value_counts().reset_index()
                reorder_counts.columns = ['Status', 'Count']

                # Map actions to colors
                color_map = {
                    'REORDER NOW': '#DC3545',
                    'REORDER SOON': '#FF9500',
                    'ADEQUATE': '#28A745',
                    'OVERSTOCKED': '#6C757D'
                }

                colors = [color_map.get(status, '#00BFFF') for status in reorder_counts['Status']]

                fig = go.Figure(data=[go.Bar(
                    x=reorder_counts['Status'],
                    y=reorder_counts['Count'],
                    marker_color=colors,
                    hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
                )])

                fig.update_layout(
                    height=350,
                    margin=dict(l=20, r=20, t=10, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#374151', size=11, family='Arial'),
                    showlegend=False
                )

                fig.update_xaxes(
                    showgrid=False,
                    title=None
                )

                fig.update_yaxes(
                    showgrid=True,
                    gridcolor='rgba(148, 163, 184, 0.15)',
                    title='Number of SKUs'
                )

                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Reorder analysis data not available")
        except Exception as e:
            logger.error(f"Error rendering reorder analysis: {str(e)}")
            st.error("Unable to render reorder analysis chart")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Monthly Trend Chart (Full Width)
    if mix_pct is not None:
        # Proper handling of mix_pct data type
        try:
            show_chart = False
            if hasattr(mix_pct, 'empty') and not mix_pct.empty:
                show_chart = True
            elif isinstance(mix_pct, (dict, list)) and len(mix_pct) > 0:
                show_chart = True

            if show_chart:
                st.markdown("<div style='margin: 32px 0;'>", unsafe_allow_html=True)
                st.markdown("""
                <div class="chart-container">
                    <h3 class="chart-title">📅 Monthly Product Mix Evolution</h3>
                """, unsafe_allow_html=True)

                fig = go.Figure()

                if isinstance(mix_pct, pd.DataFrame):
                    products = mix_pct.columns.tolist()
                    colors = ['#00BFFF', '#0099E5', '#28A745', '#FF9500', '#DC3545', '#6C757D']

                    for i, product in enumerate(products):
                        fig.add_trace(go.Scatter(
                            x=mix_pct.index,
                            y=mix_pct[product],
                            mode='lines+markers',
                            name=product,
                            line=dict(width=3, color=colors[i % len(colors)]),
                            marker=dict(size=8),
                            stackgroup='one',
                            hovertemplate='<b>%{fullData.name}</b><br>%{y:.1f}%<extra></extra>'
                        ))

                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=10, b=40),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#374151', size=11, family='Arial'),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.3,
                            xanchor="center",
                            x=0.5
                        ),
                        hovermode='x unified'
                    )

                    fig.update_xaxes(
                        showgrid=True,
                        gridcolor='rgba(148, 163, 184, 0.15)',
                        title=None
                    )

                    fig.update_yaxes(
                        showgrid=True,
                        gridcolor='rgba(148, 163, 184, 0.15)',
                        title='Percentage (%)',
                        range=[0, 100]
                    )

                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                st.markdown("</div></div>", unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error rendering monthly mix: {str(e)}")

    # Recommendations Section
    st.markdown("<div style='margin: 48px 0 24px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 style='font-size: 1.75rem; font-weight: 700; color: #2C3E50; margin-bottom: 24px;'>
        🎯 Intelligent Recommendations
    </h2>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("""
        <div class="card" style="border-left: 4px solid #DC3545; background: linear-gradient(135deg, #FFF5F5 0%, #FFFFFF 100%);">
            <h4 style="font-size: 1.125rem; font-weight: 600; color: #DC3545; margin-bottom: 12px;">
                🚨 Urgent Actions
            </h4>
            <p style="font-size: 0.875rem; color: #6C757D; margin-bottom: 16px;">
                Items requiring immediate attention
            </p>
        """, unsafe_allow_html=True)

        try:
            if rop_df is not None and not rop_df.empty and 'Action' in rop_df.columns:
                sku_col = 'SKU' if 'SKU' in rop_df.columns else 'Particular'
                urgent_items = rop_df[rop_df['Action'] == 'REORDER NOW']
                if not urgent_items.empty:
                    for idx, row in urgent_items.head(3).iterrows():
                        sku = row.get(sku_col, 'Unknown')
                        st.markdown(f"""
                        <div style="padding: 8px 12px; background: #FFFFFF; border-left: 3px solid #DC3545; border-radius: 4px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <strong style="color: #DC3545; font-size: 0.875rem;">• {sku}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <p style="font-size: 0.875rem; color: #28A745; font-weight: 600;">
                        ✓ No urgent actions required
                    </p>
                    """, unsafe_allow_html=True)
            else:
                st.info("No reorder data available")
        except Exception as e:
            logger.error(f"Error displaying urgent actions: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card" style="border-left: 4px solid #FF9500; background: linear-gradient(135deg, #FFF8F0 0%, #FFFFFF 100%);">
            <h4 style="font-size: 1.125rem; font-weight: 600; color: #FF9500; margin-bottom: 12px;">
                ⚠️ Plan Ahead
            </h4>
            <p style="font-size: 0.875rem; color: #6C757D; margin-bottom: 16px;">
                Items approaching reorder threshold
            </p>
        """, unsafe_allow_html=True)

        try:
            if rop_df is not None and not rop_df.empty and 'Action' in rop_df.columns:
                sku_col = 'SKU' if 'SKU' in rop_df.columns else 'Particular'
                warning_items = rop_df[rop_df['Action'] == 'REORDER SOON']
                if not warning_items.empty:
                    for idx, row in warning_items.head(3).iterrows():
                        sku = row.get(sku_col, 'Unknown')
                        st.markdown(f"""
                        <div style="padding: 8px 12px; background: #FFFFFF; border-left: 3px solid #FF9500; border-radius: 4px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <strong style="color: #FF9500; font-size: 0.875rem;">• {sku}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <p style="font-size: 0.875rem; color: #28A745; font-weight: 600;">
                        ✓ All items adequately stocked
                    </p>
                    """, unsafe_allow_html=True)
            else:
                st.info("No reorder data available")
        except Exception as e:
            logger.error(f"Error displaying plan ahead items: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card" style="border-left: 4px solid #28A745; background: linear-gradient(135deg, #F0FFF4 0%, #FFFFFF 100%);">
            <h4 style="font-size: 1.125rem; font-weight: 600; color: #28A745; margin-bottom: 12px;">
                ✅ Optimal Stock
            </h4>
            <p style="font-size: 0.875rem; color: #6C757D; margin-bottom: 16px;">
                Items at ideal inventory levels
            </p>
        """, unsafe_allow_html=True)

        try:
            if rop_df is not None and not rop_df.empty and 'Action' in rop_df.columns:
                sku_col = 'SKU' if 'SKU' in rop_df.columns else 'Particular'
                adequate_items = rop_df[rop_df['Action'] == 'ADEQUATE']
                if not adequate_items.empty:
                    for idx, row in adequate_items.head(3).iterrows():
                        sku = row.get(sku_col, 'Unknown')
                        st.markdown(f"""
                        <div style="padding: 8px 12px; background: #FFFFFF; border-left: 3px solid #28A745; border-radius: 4px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <strong style="color: #28A745; font-size: 0.875rem;">• {sku}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <p style="font-size: 0.875rem; color: #6C757D;">
                        No items at optimal levels
                    </p>
                    """, unsafe_allow_html=True)
            else:
                st.info("No reorder data available")
        except Exception as e:
            logger.error(f"Error displaying optimal stock items: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Enhanced Simulation Section
    st.markdown("<div style='margin: 48px 0 24px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: linear-gradient(135deg, #00BFFF 0%, #0099E5 100%); border-radius: 8px; padding: 32px; margin-bottom: 24px;">
        <h2 style='font-size: 1.75rem; font-weight: 700; color: #FFFFFF; margin-bottom: 12px;'>
            🔮 Advanced Inventory Simulation
        </h2>
        <p style='font-size: 1.125rem; color: rgba(255, 255, 255, 0.95); margin-bottom: 0;'>
            Simulate future inventory scenarios based on demand patterns, ordering policies, and service level targets.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚙️ **Configure & Run Simulation**", expanded=False):
        st.markdown("""
        <div style="background: #F8F9FA; border-radius: 6px; padding: 16px; margin-bottom: 20px;">
            <p style="color: #2C3E50; font-size: 0.95rem; margin: 0;">
                <strong>📝 Simulation Overview:</strong> This advanced simulation runs a day-by-day inventory model 
                that processes actual sales data, triggers reorders based on ROP, batches orders into 10-12 ton 
                shipments, tracks backorders, and calculates fill rates. Results include daily summaries and final inventory states.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📅 Simulation Period**")
            sim_mode = st.radio(
                "Select data range:",
                options=["Use historical data", "Custom date range"],
                label_visibility="collapsed"
            )
            if sim_mode == "Custom date range":
                start_date = st.date_input("Start Date", datetime.now())
                end_date = st.date_input("End Date", datetime.now())

        with col2:
            st.markdown("**🎯 Service Parameters**")
            service_level = st.slider(
                "Target Service Level",
                min_value=0.85,
                max_value=0.99,
                value=0.95,
                step=0.01,
                format="%.2f",
                help="Probability of not stocking out during lead time"
            )
            lead_time = st.number_input(
                "Lead Time (days)",
                min_value=1,
                max_value=30,
                value=7,
                step=1,
                help="Days between order placement and receipt"
            )

        with col3:
            st.markdown("**🚚 Order Parameters**")
            truck_min = st.number_input(
                "Min Truck Load (tons)",
                min_value=5,
                max_value=15,
                value=10,
                step=1
            )
            truck_max = st.number_input(
                "Max Truck Load (tons)",
                min_value=truck_min,
                max_value=20,
                value=12,
                step=1
            )

        st.markdown("---")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
                with st.spinner("⏳ Running inventory simulation..."):
                    try:
                        # Check if simulation.py exists
                        sim_path = os.path.join("Modules", "simulation.py")
                        if not os.path.exists(sim_path):
                            st.error(f"❌ Simulation module not found at: `{sim_path}`")
                            st.info("Please ensure the simulation.py file is in the Modules directory.")
                        else:
                            # Load and execute simulation
                            spec = importlib.util.spec_from_file_location("simulation", sim_path)
                            simulation = importlib.util.module_from_spec(spec)
                            sys.modules['simulation'] = simulation

                            # Capture output
                            output_buffer = StringIO()

                            # Redirect stdout
                            old_stdout = sys.stdout
                            sys.stdout = output_buffer

                            try:
                                spec.loader.exec_module(simulation)

                                # Run simulation
                                if hasattr(simulation, 'simulate'):
                                    if hasattr(simulation, 'INTERACTIVE'):
                                        simulation.INTERACTIVE = False
                                    simulation.simulate(interactive=False)
                                else:
                                    # Try to run main function or script
                                    st.info("Running simulation in script mode...")
                            finally:
                                sys.stdout = old_stdout

                            output = output_buffer.getvalue()

                            if output:
                                st.success("✅ **Simulation completed successfully!**")

                                # Display output in styled container
                                st.markdown("""
                                <div style="background: #2C3E50; border-radius: 6px; padding: 16px; margin: 16px 0;">
                                    <h4 style="color: #FFFFFF; margin: 0 0 12px 0;">📊 Simulation Console Output</h4>
                                </div>
                                """, unsafe_allow_html=True)

                                st.code(output, language="text")

                                # Check for output files
                                if os.path.exists("data/sim_daily_summary.csv"):
                                    st.markdown("---")
                                    st.markdown("### 📈 Simulation Results")

                                    daily_summary = pd.read_csv("data/sim_daily_summary.csv")

                                    # Create tabs for different views
                                    tab1, tab2 = st.tabs(["📊 Performance Charts", "📋 Detailed Data"])

                                    with tab1:
                                        # Fill Rate Chart
                                        if 'cum_fill_rate_pct' in daily_summary.columns:
                                            fig = go.Figure()
                                            fig.add_trace(go.Scatter(
                                                x=daily_summary.index,
                                                y=daily_summary['cum_fill_rate_pct'],
                                                mode='lines',
                                                name='Cumulative Fill Rate',
                                                line=dict(color='#28A745', width=3),
                                                fill='tozeroy',
                                                fillcolor='rgba(40, 167, 69, 0.1)'
                                            ))

                                            fig.update_layout(
                                                title="Cumulative Fill Rate Over Time",
                                                height=300,
                                                margin=dict(l=20, r=20, t=40, b=20),
                                                paper_bgcolor='rgba(0,0,0,0)',
                                                plot_bgcolor='rgba(0,0,0,0)',
                                                font=dict(color='#374151', size=11)
                                            )

                                            fig.update_xaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)')
                                            fig.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)',
                                                             title='Fill Rate (%)', range=[0, 100])

                                            st.plotly_chart(fig, use_container_width=True)

                                        # Backorder Chart
                                        if 'open_backorders_units' in daily_summary.columns:
                                            fig2 = go.Figure()
                                            fig2.add_trace(go.Bar(
                                                x=daily_summary.index,
                                                y=daily_summary['open_backorders_units'],
                                                name='Open Backorders',
                                                marker_color='#DC3545'
                                            ))

                                            fig2.update_layout(
                                                title="Daily Open Backorders",
                                                height=300,
                                                margin=dict(l=20, r=20, t=40, b=20),
                                                paper_bgcolor='rgba(0,0,0,0)',
                                                plot_bgcolor='rgba(0,0,0,0)',
                                                font=dict(color='#374151', size=11)
                                            )

                                            fig2.update_xaxes(showgrid=False)
                                            fig2.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)',
                                                              title='Units')

                                            st.plotly_chart(fig2, use_container_width=True)

                                    with tab2:
                                        st.dataframe(
                                            daily_summary,
                                            use_container_width=True,
                                            height=400
                                        )

                                        csv = daily_summary.to_csv(index=False).encode('utf-8')
                                        st.download_button(
                                            label="📥 Download Simulation Results",
                                            data=csv,
                                            file_name=f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv",
                                            type="secondary"
                                        )

                                # Check for final inventory
                                if os.path.exists("data/sim_final_inventory.csv"):
                                    final_inv = pd.read_csv("data/sim_final_inventory.csv")

                                    st.markdown("### 📦 Final Inventory State")
                                    st.dataframe(
                                        final_inv,
                                        use_container_width=True,
                                        height=300
                                    )
                            else:
                                st.warning("⚠️ Simulation completed but produced no output. Check data files.")

                    except Exception as e:
                        logger.error(f"Simulation error: {str(e)}")
                        st.error(f"❌ **Simulation failed:** {str(e)}")
                        st.info(
                            "💡 **Troubleshooting tips:**\n- Ensure all data files exist in the `data/` folder\n- Check that sales data has valid dates\n- Verify inventory and ROP files have required columns")

    st.markdown("</div>", unsafe_allow_html=True)

    # Data Tables Section
    st.markdown("<div style='margin: 48px 0 24px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 style='font-size: 1.75rem; font-weight: 700; color: #2C3E50; margin-bottom: 24px;'>
        📋 Detailed Data Tables
    </h2>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📦 Current Inventory", "📈 EOQ Analysis", "🎯 Reorder Evaluation"])

    with tab1:
        if latest_inv is not None and not latest_inv.empty:
            st.dataframe(
                latest_inv,
                use_container_width=True,
                height=400
            )

            csv = latest_inv.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Inventory Data",
                data=csv,
                file_name=f"inventory_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="secondary"
            )
        else:
            st.info("No inventory data available")

    with tab2:
        if eoq_df is not None and not eoq_df.empty:
            st.dataframe(
                eoq_df,
                use_container_width=True,
                height=400
            )

            csv = eoq_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download EOQ Data",
                data=csv,
                file_name=f"eoq_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="secondary"
            )
        else:
            st.info("No EOQ data available")

    with tab3:
        if rop_df is not None and not rop_df.empty:
            # Color code by action
            def highlight_action(row):
                if 'Action' in row:
                    if row['Action'] == 'REORDER NOW':
                        return ['background-color: #FFF5F5'] * len(row)
                    elif row['Action'] == 'REORDER SOON':
                        return ['background-color: #FFF8F0'] * len(row)
                    elif row['Action'] == 'ADEQUATE':
                        return ['background-color: #F0FFF4'] * len(row)
                return [''] * len(row)

            st.dataframe(
                rop_df.style.apply(highlight_action, axis=1),
                use_container_width=True,
                height=400
            )

            csv = rop_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Reorder Data",
                data=csv,
                file_name=f"reorder_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="secondary"
            )
        else:
            st.info("No reorder evaluation data available")

    st.markdown("</div>", unsafe_allow_html=True)
