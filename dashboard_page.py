
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
            <h3 class="" style="color: #000000;">📈 Daily Sales Trend</h3>
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

        # Get date range from sales data
        min_date = None
        max_date = None
        if sales_df is not None and not sales_df.empty and 'Date' in sales_df.columns:
            try:
                sales_df_temp = sales_df.copy()
                sales_df_temp['Date'] = pd.to_datetime(sales_df_temp['Date'], errors='coerce', dayfirst=True)
                sales_df_temp = sales_df_temp.dropna(subset=['Date'])

                if not sales_df_temp.empty:
                    min_date = sales_df_temp['Date'].min().date()
                    max_date = sales_df_temp['Date'].max().date()
            except Exception as e:
                logger.error(f"Error parsing sales dates: {str(e)}")
                min_date = datetime.now().date()
                max_date = datetime.now().date()

        if min_date is None:
            min_date = datetime.now().date()
            max_date = datetime.now().date()

        # Parameter Configuration in 3 columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📅 Simulation Period**")
            sim_mode = st.radio(
                "Select data range:",
                options=["Use historical data", "Custom date range"],
                help="Choose whether to use all historical data or specify a custom date range"
            )

            start_date = min_date
            end_date = max_date

            if sim_mode == "Custom date range":
                st.markdown(f"*Available data: {min_date} to {max_date}*")

                start_date = st.date_input(
                    "Start Date",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    help=f"Select start date (between {min_date} and {max_date})"
                )

                end_date = st.date_input(
                    "End Date",
                    value=max_date,
                    min_value=start_date,
                    max_value=max_date,
                    help=f"Select end date (between {start_date} and {max_date})"
                )

                # Validate date range
                if start_date >= end_date:
                    st.warning("⚠️ End date must be after start date")

                sim_days = (end_date - start_date).days
                st.info(f"📊 Simulation will run for **{sim_days} days**")

        with col2:
            st.markdown("**🎯 Service & Risk Parameters**")

            service_level = st.slider(
                "Target Service Level",
                min_value=0.80,
                max_value=0.99,
                value=0.95,
                step=0.01,
                format="%.2f",
                help="Probability of not stocking out during lead time (higher = more safety stock)"
            )

            lead_time = st.number_input(
                "Lead Time (days)",
                min_value=1,
                max_value=30,
                value=7,
                step=1,
                help="Days between order placement and receipt"
            )

            demand_variability = st.slider(
                "Demand Variability Factor",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                format="%.1f",
                help="Multiplier for demand variance (1.0 = historical, >1.0 = more volatile)"
            )

            stockout_cost = st.number_input(
                "Stockout Cost per Unit",
                min_value=0.0,
                max_value=1000.0,
                value=50.0,
                step=10.0,
                help="Cost penalty for each unit of unmet demand"
            )

        with col3:
            st.markdown("**🚚 Ordering & Logistics**")

            truck_min = st.number_input(
                "Min Truck Load (tons)",
                min_value=1,
                max_value=20,
                value=10,
                step=1,
                help="Minimum truck capacity for economic shipping"
            )

            truck_max = st.number_input(
                "Max Truck Load (tons)",
                min_value=truck_min,
                max_value=25,
                value=12,
                step=1,
                help="Maximum truck capacity"
            )

            ordering_cost = st.number_input(
                "Fixed Ordering Cost",
                min_value=0.0,
                max_value=5000.0,
                value=500.0,
                step=50.0,
                help="Fixed cost per order regardless of quantity"
            )

            holding_cost_rate = st.slider(
                "Holding Cost Rate (%/year)",
                min_value=5.0,
                max_value=50.0,
                value=20.0,
                step=1.0,
                format="%.1f%%",
                help="Annual inventory holding cost as percentage of item value"
            )

        # Advanced Options (collapsible)
        with st.expander("🔧 **Advanced Simulation Options**", expanded=False):
            col_adv1, col_adv2 = st.columns(2)

            with col_adv1:
                st.markdown("**📊 Analysis Settings**")

                random_seed = st.number_input(
                    "Random Seed",
                    min_value=1,
                    max_value=9999,
                    value=42,
                    help="Seed for reproducible results"
                )

                monte_carlo_runs = st.selectbox(
                    "Monte Carlo Iterations",
                    options=[1, 10, 50, 100],
                    index=0,
                    help="Number of simulation runs for statistical analysis"
                )

                confidence_interval = st.slider(
                    "Confidence Interval",
                    min_value=80,
                    max_value=99,
                    value=95,
                    step=1,
                    format="%d%%",
                    help="Confidence level for statistical results"
                )

            with col_adv2:
                st.markdown("**⚙️ Operational Settings**")

                safety_stock_method = st.selectbox(
                    "Safety Stock Method",
                    options=["Statistical", "Fixed Days", "Percentage"],
                    index=0,
                    help="Method for calculating safety stock levels"
                )

                reorder_policy = st.selectbox(
                    "Reorder Policy",
                    options=["(s,S) Policy", "Periodic Review", "Continuous Review"],
                    index=0,
                    help="Inventory replenishment policy"
                )

                enable_rush_orders = st.checkbox(
                    "Enable Rush Orders",
                    value=False,
                    help="Allow emergency orders with reduced lead time at higher cost"
                )

        st.markdown("---")

        # Simulation Configuration Summary
        st.markdown("### 📋 Simulation Configuration Summary")

        sum_col1, sum_col2, sum_col3 = st.columns(3)

        with sum_col1:
            st.markdown(f"""
            **📅 Time Period:**
            - Mode: {sim_mode}
            - Start: {start_date}
            - End: {end_date}
            - Duration: {(end_date - start_date).days} days
            """)

        with sum_col2:
            st.markdown(f"""
            **🎯 Service Level:**
            - Target: {service_level:.1%}
            - Lead Time: {lead_time} days
            - Demand Variability: {demand_variability}x
            - Stockout Cost: ${stockout_cost:.0f}/unit
            """)

        with sum_col3:
            st.markdown(f"""
            **🚚 Logistics:**
            - Truck Range: {truck_min}-{truck_max} tons
            - Ordering Cost: ${ordering_cost:.0f}
            - Holding Rate: {holding_cost_rate:.1f}%/year
            - Monte Carlo: {monte_carlo_runs} runs
            """)

        st.markdown("---")

        # Run button in centered column
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            run_simulation = st.button("🚀 Run Simulation", type="primary", use_container_width=True)

        # IMPORTANT: Break out of columns for results by using full width container
        if run_simulation:
            # Validate inputs before running
            if sim_mode == "Custom date range" and start_date >= end_date:
                st.error("❌ **Invalid date range!** End date must be after start date.")
                return

            with st.spinner("⏳ Running inventory simulation..."):
                try:
                    # Check if simulation.py exists
                    sim_path = os.path.join("Modules", "simulation.py")
                    if not os.path.exists(sim_path):
                        st.error(f"❌ Simulation module not found at: `{sim_path}`")
                        st.info("Please ensure the simulation.py file is in the Modules directory.")
                    else:
                        # Pass parameters to simulation (if the module supports it)
                        simulation_params = {
                            'start_date': start_date,
                            'end_date': end_date,
                            'service_level': service_level,
                            'lead_time': lead_time,
                            'truck_min': truck_min,
                            'truck_max': truck_max,
                            'ordering_cost': ordering_cost,
                            'holding_cost_rate': holding_cost_rate / 100,  # Convert to decimal
                            'stockout_cost': stockout_cost,
                            'demand_variability': demand_variability,
                            'random_seed': random_seed,
                            'monte_carlo_runs': monte_carlo_runs,
                            'safety_stock_method': safety_stock_method,
                            'reorder_policy': reorder_policy,
                            'enable_rush_orders': enable_rush_orders
                        }

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

                            # Try to pass parameters to simulation if it supports them
                            if hasattr(simulation, 'run_simulation_with_params'):
                                simulation.run_simulation_with_params(simulation_params)
                            elif hasattr(simulation, 'simulate'):
                                if hasattr(simulation, 'INTERACTIVE'):
                                    simulation.INTERACTIVE = False
                                simulation.simulate(interactive=False)
                            else:
                                # Try to run main function or script
                                st.info("Running simulation in script mode...")
                        finally:
                            sys.stdout = old_stdout

                        output = output_buffer.getvalue()

                        # Store console output in session state
                        st.session_state['sim_console_output'] = output

                        if output:
                            st.success("✅ **Simulation completed successfully!**")

                            # FULL WIDTH RESULTS SECTION - OUTSIDE EXPANDER COLUMNS
                            st.markdown("</div>", unsafe_allow_html=True)  # Close expander div if needed

                            # Create full-width container for results
                            st.markdown("""
                            <div style='margin: 24px 0; padding: 0;'>
                                <h3 style='font-size: 1.5rem; font-weight: 700; color: #2C3E50; margin-bottom: 24px; text-align: center;'>
                                    📊 Simulation Results
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)

                            # Initialize tabs list
                            tab_names = []

                            # Check what results are available
                            has_daily_summary = os.path.exists("data/sim_daily_summary.csv")
                            has_final_inventory = os.path.exists("data/sim_final_inventory.csv")

                            # Build tab list based on available results
                            if has_daily_summary:
                                tab_names.extend(["📊 Performance Charts", "📋 Daily Summary"])
                            if has_final_inventory:
                                tab_names.append("📦 Final Inventory")

                            # Always include console logs tab
                            tab_names.append("🖥️ Console Logs")

                            # Create FULL WIDTH tabs
                            if len(tab_names) > 1:
                                tabs = st.tabs(tab_names)
                                tab_index = 0

                                # Performance Charts Tab
                                if has_daily_summary:
                                    with tabs[tab_index]:
                                        daily_summary = pd.read_csv("data/sim_daily_summary.csv")

                                        # Create two columns for charts
                                        chart_col1, chart_col2 = st.columns(2, gap="large")

                                        # Fill Rate Chart
                                        with chart_col1:
                                            if 'cum_fill_rate_pct' in daily_summary.columns:
                                                st.markdown("#### 📈 Cumulative Fill Rate")
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
                                                    height=350,
                                                    margin=dict(l=20, r=20, t=20, b=20),
                                                    paper_bgcolor='rgba(0,0,0,0)',
                                                    plot_bgcolor='rgba(0,0,0,0)',
                                                    font=dict(color='#374151', size=11)
                                                )

                                                fig.update_xaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)')
                                                fig.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)',
                                                                 title='Fill Rate (%)', range=[0, 100])

                                                st.plotly_chart(fig, use_container_width=True,
                                                                config={'displayModeBar': False})

                                        # Backorder Chart
                                        with chart_col2:
                                            if 'open_backorders_units' in daily_summary.columns:
                                                st.markdown("#### 📉 Daily Backorders")
                                                fig2 = go.Figure()
                                                fig2.add_trace(go.Bar(
                                                    x=daily_summary.index,
                                                    y=daily_summary['open_backorders_units'],
                                                    name='Open Backorders',
                                                    marker_color='#DC3545'
                                                ))

                                                fig2.update_layout(
                                                    height=350,
                                                    margin=dict(l=20, r=20, t=20, b=20),
                                                    paper_bgcolor='rgba(0,0,0,0)',
                                                    plot_bgcolor='rgba(0,0,0,0)',
                                                    font=dict(color='#374151', size=11)
                                                )

                                                fig2.update_xaxes(showgrid=False)
                                                fig2.update_yaxes(showgrid=True, gridcolor='rgba(148, 163, 184, 0.15)',
                                                                  title='Units')

                                                st.plotly_chart(fig2, use_container_width=True,
                                                                config={'displayModeBar': False})

                                    tab_index += 1

                                # Daily Summary Tab
                                if has_daily_summary:
                                    with tabs[tab_index]:
                                        daily_summary = pd.read_csv("data/sim_daily_summary.csv")

                                        st.markdown("#### 📈 Detailed Daily Summary")
                                        st.dataframe(
                                            daily_summary,
                                            use_container_width=True,
                                            height=500
                                        )

                                        csv = daily_summary.to_csv(index=False).encode('utf-8')
                                        st.download_button(
                                            label="📥 Download Daily Summary",
                                            data=csv,
                                            file_name=f"sim_daily_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv",
                                            type="secondary"
                                        )

                                    tab_index += 1

                                # Final Inventory Tab
                                if has_final_inventory:
                                    with tabs[tab_index]:
                                        final_inv = pd.read_csv("data/sim_final_inventory.csv")

                                        st.markdown("#### 📦 Final Inventory State")
                                        st.dataframe(
                                            final_inv,
                                            use_container_width=True,
                                            height=500
                                        )

                                        csv_final = final_inv.to_csv(index=False).encode('utf-8')
                                        st.download_button(
                                            label="📥 Download Final Inventory",
                                            data=csv_final,
                                            file_name=f"sim_final_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv",
                                            type="secondary"
                                        )

                                    tab_index += 1

                                # Console Logs Tab - GET FROM SESSION STATE
                                with tabs[tab_index]:
                                    st.markdown("#### 🖥️ Simulation Console Output")

                                    console_output = st.session_state.get('sim_console_output', '')
                                    if console_output:
                                        st.code(console_output, language="text", line_numbers=True)

                                        # Download console output
                                        st.download_button(
                                            label="📥 Download Console Logs",
                                            data=console_output.encode('utf-8'),
                                            file_name=f"sim_console_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                            mime="text/plain",
                                            type="secondary"
                                        )
                                    else:
                                        st.info("No console output available")
                            else:
                                # If only console logs, show them directly
                                st.markdown("#### 🖥️ Simulation Console Output")
                                console_output = st.session_state.get('sim_console_output', '')
                                if console_output:
                                    st.code(console_output, language="text", line_numbers=True)
                                else:
                                    st.info("No console output available")

                            # Summary metrics if available - FULL WIDTH
                            if has_daily_summary:
                                daily_summary = pd.read_csv("data/sim_daily_summary.csv")

                                st.markdown("---")
                                st.markdown("#### 📊 Key Simulation Metrics")

                                # Full width metrics in 4 columns
                                met_col1, met_col2, met_col3, met_col4 = st.columns(4, gap="medium")

                                with met_col1:
                                    if 'cum_fill_rate_pct' in daily_summary.columns:
                                        final_fill_rate = daily_summary['cum_fill_rate_pct'].iloc[-1]
                                        st.metric(
                                            label="🎯 Final Fill Rate",
                                            value=f"{final_fill_rate:.1f}%",
                                            delta=None
                                        )

                                with met_col2:
                                    if 'open_backorders_units' in daily_summary.columns:
                                        max_backorders = daily_summary['open_backorders_units'].max()
                                        st.metric(
                                            label="📉 Peak Backorders",
                                            value=f"{max_backorders:,.0f}",
                                            delta=None
                                        )

                                with met_col3:
                                    simulation_days = len(daily_summary)
                                    st.metric(
                                        label="📅 Simulation Days",
                                        value=f"{simulation_days}",
                                        delta=None
                                    )

                                with met_col4:
                                    if 'orders_placed' in daily_summary.columns:
                                        total_orders = daily_summary['orders_placed'].sum()
                                        st.metric(
                                            label="🚚 Total Orders",
                                            value=f"{total_orders:,.0f}",
                                            delta=None
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
