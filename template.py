# template.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------- Styles ----------
def inject_css():
    st.markdown("""
    <style>
    :root{
      --gap: 16px; --gap-lg: 22px;
      --bg: #0b1220; --card:#0f172a; --muted:#94a3b8; --text:#e2e8f0;
    }
    html, body, [data-testid="stAppViewContainer"]{
      background: var(--bg); color: var(--text);
      padding: 12px 18px;
    }
    div[data-testid="stHorizontalBlock"]{ margin-left: -10px; margin-right: -10px; }
    div[data-testid="column"]{ padding-left: 10px; padding-right: 10px; }

    .section-title{ font-size:22px; font-weight:700; margin: 2px 0 10px; }
    .h2{ font-size:16px; font-weight:600; margin: 16px 0 10px; }
    .small{ color: var(--muted); font-size: 12px; }

    div[data-testid="stPlotlyChart"],
    div[data-testid="stDataFrame"],
    div[data-testid="stMetric"],
    div[data-baseweb="notification"]{
      border: 1px solid rgba(148,163,184,0.12);
      background: var(--card);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: var(--gap-lg);
      box-shadow: 0 0 0 1px rgba(99,102,241,0.05), 0 8px 24px rgba(2,6,23,0.45);
      overflow: hidden;
    }
    div[data-testid="stMetric"]{ padding: 18px; }
    div[data-testid="stMetricLabel"] p { color: #94a3b8 !important; font-size: 13px; margin-bottom: 6px; }
    div[data-testid="stMetricValue"]   { color: #e2e8f0 !important; font-size: 28px; font-weight: 800; }
    div[data-testid="stMetricDelta"]   { color: #86efac !important; font-weight: 600; }
    div[data-testid="stMetricDelta"] span{
      background: rgba(34,197,94,0.15); padding: 2px 8px; border-radius: 999px;
    }
    .js-plotly-plot .modebar{
      top: 8px !important; right: 8px !important;
      background: rgba(2,6,23,0.35) !important; border-radius: 8px;
    }
    a.cta, button.cta {
      display:inline-block; background:#6366f1; color:#0b1220; padding:10px 14px; 
      border-radius:10px; text-decoration:none; font-weight:700; border:none;
    }
    a.cta:hover, button.cta:hover { filter:brightness(1.1); }
    .hero{
      border: 1px solid rgba(148,163,184,0.12);
      background: #0f172a;
      border-radius: 14px;
      padding: 18px;
      margin-bottom: 20px;
      box-shadow: 0 0 0 1px rgba(99,102,241,0.05), 0 8px 24px rgba(2,6,23,0.45);
    }
    </style>
    """, unsafe_allow_html=True)
# ---------- Home (Landing) ----------
def render_home():
    st.markdown('<div class="section-title">SecondBrainn for Inventory</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero">Drive lower carrying costs and fewer stockouts with AI-backed reorder plans and live dashboards.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### What’s inside")
        st.markdown("- Real-time EOQ and ROP suggestions\n- Inventory timeline and category mix\n- Downloadable tables and interactive charts")
        st.markdown('<a class="cta" href="#dashboard">Go to Dashboard</a>', unsafe_allow_html=True)
    with c2:
        st.markdown("#### Getting started")
        st.markdown("- Place data files in ./data (Sales, Purchase, Base Inventory)\n- Use sidebar Controls, then click Rebuild\n- Toggle sections via Dashboard sections")

# ---------- KPI cards ----------
def kpis(sales_df: pd.DataFrame, rop_df: pd.DataFrame):
    col1, col2, col3, col4 = st.columns(4)
    total_rev = 0.0
    if sales_df is not None and {"Quantity","Rate"}.issubset(sales_df.columns):
        total_rev = float((sales_df["Quantity"] * sales_df["Rate"]).sum())
    active = int(rop_df["need_reorder"].sum()) if rop_df is not None and "need_reorder" in rop_df.columns else 0
    with col1: st.metric(label="Total Revenue", value=f"₹{total_rev:,.0f}", delta="+12.5%")
    with col2: st.metric(label="Active Orders", value=f"{active}", delta="+8.2%")
    with col3: st.metric(label="Efficiency Score", value="94%", delta="+3.1%")
    with col4: st.metric(label="Cost Savings", value="₹12,450", delta="+15.8%")

# ---------- Charts / Tables ----------
def chart_sales_vs_orders(sales_df: pd.DataFrame):
    st.markdown('<div class="h2">Sales vs Orders</div>', unsafe_allow_html=True)
    s = sales_df.copy()
    s["Date"] = pd.to_datetime(s["Date"])
    monthly = s.groupby(s["Date"].dt.to_period("M")).agg(Sales=("Value","sum"), Orders=("Quantity","sum")).reset_index()
    monthly["Date"] = monthly["Date"].dt.to_timestamp()
    fig = go.Figure()
    fig.add_bar(x=monthly["Date"], y=monthly["Sales"], name="Sales", marker_color="#6366f1")
    fig.add_scatter(x=monthly["Date"], y=monthly["Orders"], name="Orders", mode="lines+markers", line=dict(color="#06b6d4", width=2))
    fig.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,24,39,1)", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True, theme=None)

def chart_inventory_trend(latest_inv: pd.DataFrame, eoq_df: pd.DataFrame):
    st.markdown('<div class="h2">Inventory trend</div>', unsafe_allow_html=True)
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

def chart_category_mix(sales_df: pd.DataFrame):
    st.markdown('<div class="h2">Category mix</div>', unsafe_allow_html=True)
    def extract(pt):
        for t in ["DWR","DIR","HDHMR"]:
            if isinstance(pt, str) and t in pt: return t
        return "OTHER"
    s = sales_df.copy()
    s["Category"] = s["Particular"].apply(extract)
    pie = s.groupby("Category")["Quantity"].sum().reset_index()
    fig3 = px.pie(pie, names="Category", values="Quantity",
                  color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b","#ef4444"])
    fig3.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                       paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
    st.plotly_chart(fig3, use_container_width=True, theme=None)

def chart_eoq(eoq_df: pd.DataFrame):
    st.markdown('<div class="h2">EOQ by SKU</div>', unsafe_allow_html=True)
    top = eoq_df.sort_values("EOQ", ascending=False).head(15)
    fig = px.bar(top, x="Particular", y="EOQ", color_discrete_sequence=["#6366f1"])
    fig.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                      paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True, theme=None)

def table_inventory_vs_rop(rop_df: pd.DataFrame):
    st.markdown('<div class="h2">Inventory vs ROP</div>', unsafe_allow_html=True)
    table = rop_df[["Particular","inventory_position","reorder_point","need_reorder","suggested_order_qty"]] \
            .sort_values(["need_reorder","Particular"], ascending=[False, True])
    st.dataframe(table, use_container_width=True)

def table_reorder_suggestions(rop_df: pd.DataFrame):
    st.markdown('<div class="h2">Reorder suggestions</div>', unsafe_allow_html=True)
    suggest = rop_df[rop_df["need_reorder"] == True][["Particular","suggested_order_qty","EOQ","lead_time_days","service_level"]]
    st.dataframe(suggest.sort_values("suggested_order_qty", ascending=False), use_container_width=True)

def chart_monthly_mix(mix_pct: pd.DataFrame):
    st.markdown('<div class="h2">Monthly mix</div>', unsafe_allow_html=True)
    mp = mix_pct.reset_index().melt(id_vars="YearMonth", var_name="Type", value_name="Pct")
    mp["YearMonth"] = mp["YearMonth"].astype(str)
    fig = px.area(mp, x="YearMonth", y="Pct", color="Type",
                  color_discrete_sequence=["#6366f1","#06b6d4","#22c55e","#f59e0b"])
    fig.update_layout(height=320, margin=dict(l=24, r=18, t=26, b=26),
                      paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
    st.plotly_chart(fig, use_container_width=True, theme=None)

# ---------- Dashboard compositor ----------
def render_dashboard(sales_df, latest_inv, eoq_df, rop_df, mix_pct, visible_sections):
    if "KPIs" in visible_sections:
        kpis(sales_df, rop_df)
    cols_top = st.columns((7,6,6))
    with cols_top[0]:
        if "Sales vs Orders" in visible_sections and sales_df is not None and not sales_df.empty and {"Date","Quantity"}.issubset(sales_df.columns):
            chart_sales_vs_orders(sales_df)
    with cols_top[1]:
        if "Inventory trend" in visible_sections and latest_inv is not None and not latest_inv.empty:
            chart_inventory_trend(latest_inv, eoq_df if eoq_df is not None else pd.DataFrame())
    with cols_top[2]:
        if "Category mix" in visible_sections and sales_df is not None and not sales_df.empty:
            chart_category_mix(sales_df)

    cols_bottom = st.columns((7,7))
    with cols_bottom[0]:
        if "EOQ by SKU" in visible_sections and eoq_df is not None and not eoq_df.empty:
            chart_eoq(eoq_df)
    with cols_bottom[1]:
        if "Monthly mix" in visible_sections and mix_pct is not None and not mix_pct.empty:
            chart_monthly_mix(mix_pct)

    if "Inventory vs ROP" in visible_sections and rop_df is not None and not rop_df.empty and {"Particular","inventory_position","reorder_point"}.issubset(rop_df.columns):
        table_inventory_vs_rop(rop_df)
    if "Reorder suggestions" in visible_sections and rop_df is not None and not rop_df.empty and "need_reorder" in rop_df.columns:
        table_reorder_suggestions(rop_df)
