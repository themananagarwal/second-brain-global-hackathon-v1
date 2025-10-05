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
            <h3 class="chart-title">Sales Trend Analysis</h3>
        """, unsafe_allow_html=True)

        try:
            if 'Date' in sales_df.columns and 'Quantity' in sales_df.columns:
                # Prepare daily sales data
                sales_df_copy = sales_df.copy()
                sales_df_copy['Date'] = pd.to_datetime(sales_df_copy['Date'])
                daily_sales = sales_df_copy.groupby('Date')['Quantity'].sum().reset_index()
                daily_sales = daily_sales.sort_values('Date')

                # Create area chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_sales['Date'],
                    y=daily_sales['Quantity'],
                    mode='lines',
                    name='Sales Volume',
                    fill='tozeroy',
                    fillcolor='rgba(0, 191, 255, 0.1)',
                    line=dict(color='#00BFFF', width=2)
                ))

                fig.update_layout(
                    height=400,
                    margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#374151', size=12),
                    showlegend=False,
                    hovermode='x unified'
                )

                fig.update_xaxes(
                    showgrid=True,
                    gridcolor='rgba(148, 163, 184, 0.1)',
                    title=None
                )

                fig.update_yaxes(
                    showgrid=True,
                    gridcolor='rgba(148, 163, 184, 0.1)',
                    title='Quantity'
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sales trend data not available")
        except Exception as e:
            logger.error(f"Error rendering sales trend: {str(e)}")
            st.error("Unable to render sales trend chart")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="chart-container">
            <h3 class="chart-title">Product Mix Distribution</h3>
        """, unsafe_allow_html=True)

        try:
            if 'Particular' in sales_df.columns and 'Quantity' in sales_df.columns:
                # Calculate product mix
                product_mix = sales_df.groupby('Particular')['Quantity'].sum().reset_index()
                product_mix = product_mix.sort_values('Quantity', ascending=False)

                # Create donut chart
                fig = go.Figure(data=[go.Pie(
                    labels=product_mix['Particular'],
                    values=product_mix['Quantity'],
                    hole=0.5,
                    marker=dict(
                        colors=['#00BFFF', '#0099E5', '#28A745', '#FF9500', '#DC3545'],
                        line=dict(color='white', width=2)
                    ),
                    textposition='outside',
                    textinfo='label+percent'
                )])

                fig.update_layout(
                    height=400,
                    margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#374151', size=12),
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)
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
            <h3 class="chart-title">Current vs Optimal Inventory</h3>
        """, unsafe_allow_html=True)

        try:
            if latest_inv is not None and not latest_inv.empty and eoq_df is not None and not eoq_df.empty:
                # Merge inventory with EOQ data
                if 'SKU' in latest_inv.columns and 'SKU' in eoq_df.columns:
                    inv_comparison = latest_inv.merge(
                        eoq_df[['SKU', 'EOQ']],
                        left_on='SKU',
                        right_on='SKU',
                        how='left'
                    )

                    if 'Current_Stock' in inv_comparison.columns and 'EOQ' in inv_comparison.columns:
                        inv_comparison = inv_comparison.head(10)  # Top 10 SKUs

                        fig = go.Figure()

                        fig.add_trace(go.Bar(
                            name='Current Stock',
                            x=inv_comparison['SKU'],
                            y=inv_comparison['Current_Stock'],
                            marker_color='#00BFFF'
                        ))

                        fig.add_trace(go.Bar(
                            name='Optimal (EOQ)',
                            x=inv_comparison['SKU'],
                            y=inv_comparison['EOQ'],
                            marker_color='#28A745'
                        ))

                        fig.update_layout(
                            height=400,
                            margin=dict(l=10, r=10, t=30, b=10),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#374151', size=12),
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
                            title=None
                        )

                        fig.update_yaxes(
                            showgrid=True,
                            gridcolor='rgba(148, 163, 184, 0.1)',
                            title='Quantity'
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Inventory comparison data incomplete")
                else:
                    st.info("SKU columns not found in inventory data")
            else:
                st.info("Inventory or EOQ data not available")
        except Exception as e:
            logger.error(f"Error rendering inventory comparison: {str(e)}")
            st.error("Unable to render inventory comparison chart")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="chart-container">
            <h3 class="chart-title">Reorder Priority Analysis</h3>
        """, unsafe_allow_html=True)

        try:
            if rop_df is not None and not rop_df.empty:
                # Check for reorder recommendations
                if 'Action' in rop_df.columns:
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
                        text=reorder_counts['Count'],
                        textposition='outside'
                    )])

                    fig.update_layout(
                        height=400,
                        margin=dict(l=10, r=10, t=30, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#374151', size=12),
                        showlegend=False
                    )

                    fig.update_xaxes(
                        showgrid=False,
                        title=None
                    )

                    fig.update_yaxes(
                        showgrid=True,
                        gridcolor='rgba(148, 163, 184, 0.1)',
                        title='Number of SKUs'
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Reorder action data not available")
            else:
                st.info("Reorder analysis data not available")
        except Exception as e:
            logger.error(f"Error rendering reorder analysis: {str(e)}")
            st.error("Unable to render reorder analysis chart")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Recommendations Section
    st.markdown("<div style='margin: 48px 0 24px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 style='font-size: 1.75rem; font-weight: 700; color: #2C3E50; margin-bottom: 24px;'>
        Intelligent Recommendations
    </h2>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("""
        <div class="card" style="border-left: 4px solid #DC3545;">
            <h4 style="font-size: 1.125rem; font-weight: 600; color: #DC3545; margin-bottom: 12px;">
                🚨 Urgent Actions
            </h4>
            <p style="font-size: 0.875rem; color: #6C757D; margin-bottom: 16px;">
                Items requiring immediate attention
            </p>
        """, unsafe_allow_html=True)

        try:
            if rop_df is not None and not rop_df.empty and 'Action' in rop_df.columns:
                urgent_items = rop_df[rop_df['Action'] == 'REORDER NOW']
                if not urgent_items.empty:
                    for idx, row in urgent_items.head(3).iterrows():
                        sku = row.get('SKU', 'Unknown')
                        st.markdown(f"""
                        <div style="padding: 8px; background: #FFF5F5; border-radius: 4px; margin-bottom: 8px;">
                            <strong style="color: #DC3545;">• {sku}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <p style="font-size: 0.875rem; color: #28A745;">
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
        <div class="card" style="border-left: 4px solid #FF9500;">
            <h4 style="font-size: 1.125rem; font-weight: 600; color: #FF9500; margin-bottom: 12px;">
                ⚠️ Plan Ahead
            </h4>
            <p style="font-size: 0.875rem; color: #6C757D; margin-bottom: 16px;">
                Items approaching reorder threshold
            </p>
        """, unsafe_allow_html=True)

        try:
            if rop_df is not None and not rop_df.empty and 'Action' in rop_df.columns:
                warning_items = rop_df[rop_df['Action'] == 'REORDER SOON']
                if not warning_items.empty:
                    for idx, row in warning_items.head(3).iterrows():
                        sku = row.get('SKU', 'Unknown')
                        st.markdown(f"""
                        <div style="padding: 8px; background: #FFF8F0; border-radius: 4px; margin-bottom: 8px;">
                            <strong style="color: #FF9500;">• {sku}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <p style="font-size: 0.875rem; color: #28A745;">
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
        <div class="card" style="border-left: 4px solid #28A745;">
            <h4 style="font-size: 1.125rem; font-weight: 600; color: #28A745; margin-bottom: 12px;">
                ✅ Optimal Stock
            </h4>
            <p style="font-size: 0.875rem; color: #6C757D; margin-bottom: 16px;">
                Items at ideal inventory levels
            </p>
        """, unsafe_allow_html=True)

        try:
            if rop_df is not None and not rop_df.empty and 'Action' in rop_df.columns:
                adequate_items = rop_df[rop_df['Action'] == 'ADEQUATE']
                if not adequate_items.empty:
                    for idx, row in adequate_items.head(3).iterrows():
                        sku = row.get('SKU', 'Unknown')
                        st.markdown(f"""
                        <div style="padding: 8px; background: #F0FFF4; border-radius: 4px; margin-bottom: 8px;">
                            <strong style="color: #28A745;">• {sku}</strong>
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

    # Simulation Section
    st.markdown("<div style='margin: 48px 0 24px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <h2 style='font-size: 1.75rem; font-weight: 700; color: #2C3E50; margin-bottom: 16px;'>
        📊 Inventory Simulation
    </h2>
    <p style='font-size: 1.125rem; color: #6C757D; margin-bottom: 24px;'>
        Simulate future inventory scenarios based on demand patterns and ordering policies.
    </p>
    """, unsafe_allow_html=True)

    with st.expander("🔮 **Run Simulation**", expanded=False):
        st.markdown("**Configure simulation parameters:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            sim_days = st.number_input("Simulation Days", min_value=30, max_value=365, value=90, step=30)

        with col2:
            service_level = st.slider("Service Level", min_value=0.85, max_value=0.99, value=0.95, step=0.01)

        with col3:
            lead_time = st.number_input("Lead Time (days)", min_value=1, max_value=30, value=7, step=1)

        if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
            with st.spinner("Running simulation..."):
                try:
                    # Check if simulation.py exists
                    sim_path = os.path.join("Modules", "simulation.py")
                    if os.path.exists(sim_path):
                        # Load simulation module
                        spec = importlib.util.spec_from_file_location("simulation", sim_path)
                        simulation = importlib.util.module_from_spec(spec)

                        # Capture output
                        output_buffer = StringIO()
                        with redirect_stdout(output_buffer):
                            spec.loader.exec_module(simulation)

                        output = output_buffer.getvalue()

                        if output:
                            st.success("✅ Simulation completed successfully!")
                            st.text_area("Simulation Output", output, height=300)
                        else:
                            st.warning("Simulation completed but produced no output")
                    else:
                        st.error(f"Simulation module not found at {sim_path}")
                except Exception as e:
                    logger.error(f"Simulation error: {str(e)}")
                    st.error(f"Simulation failed: {str(e)}")

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
            st.dataframe(
                rop_df,
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
