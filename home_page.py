# home_page.py
import streamlit as st


def render_home_page():
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">
            Your Business<br>
            Optimization<br>
            Engine
        </div>
        <div class="hero-subtitle">
            Skip the prescriptive processes. Let AI make intelligent decisions for your business. 
            From inventory optimization to operational efficiency - your second brain handles it all.
        </div>
        <div class="hero-buttons">
            <a href="#" class="btn btn-primary" style="background: white; color: #0ea5e9;">Get Started Today →</a>
            <a href="#" class="btn btn-secondary" style="background: white; color: #0ea5e9;">Schedule Demo</a>
        </div>
        <div style="margin-top: 2rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <div class="cta-feature" style="color: rgba(255,255,255,0.8);">
                <span>❄️</span> 14-day free trial
            </div>
            <div class="cta-feature" style="color: rgba(255,255,255,0.8);">
                <span>❄️</span> No credit card required
            </div>
            <div class="cta-feature" style="color: rgba(255,255,255,0.8);">
                <span>❄️</span> Setup in minutes
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Features Section
    st.markdown("""
    <div class="page-header" style="margin-top: 4rem;">
        <h2 style="color: var(--gray-800); font-size: 2.5rem; font-weight: 700;">
            Intelligent Business <span style="color: var(--primary-cyan);">Automation</span>
        </h2>
        <p style="color: var(--gray-600); font-size: 1.1rem; max-width: 800px; margin: 1rem auto;">
            Replace manual decision-making with AI-powered intelligence. See how Second Brain 
            transforms businesses across industries.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3 class="feature-title">AI-Powered Decision Making</h3>
            <p class="feature-description">
                Advanced algorithms analyze your business patterns and make optimal decisions automatically.
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem 1rem; background: #f0f9ff; border-radius: 0.5rem; display: inline-block;">
                <span style="color: #0ea5e9; font-weight: 600; font-size: 0.875rem;">Core Feature</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <h3 class="feature-title">Inventory Optimization</h3>
            <p class="feature-description">
                Know exactly when to order, how much to order, and in what combinations for maximum efficiency.
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem 1rem; background: #fef3c7; border-radius: 0.5rem; display: inline-block;">
                <span style="color: #d97706; font-weight: 600; font-size: 0.875rem;">Popular</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⏰</div>
            <h3 class="feature-title">Real-Time Monitoring</h3>
            <p class="feature-description">
                Continuous tracking of your business metrics with instant alerts when action is needed.
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem 1rem; background: #f0fdf4; border-radius: 0.5rem; display: inline-block;">
                <span style="color: #16a34a; font-weight: 600; font-size: 0.875rem;">24/7</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Second Row of Features
    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔮</div>
            <h3 class="feature-title">Predictive Analytics</h3>
            <p class="feature-description">
                Forecast demand, identify trends, and prepare for market changes before they happen.
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem 1rem; background: #f3e8ff; border-radius: 0.5rem; display: inline-block;">
                <span style="color: #7c3aed; font-weight: 600; font-size: 0.875rem;">Smart</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3 class="feature-title">Business Intelligence</h3>
            <p class="feature-description">
                Transform raw data into actionable insights with beautiful, intuitive dashboards.
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem 1rem; background: #fef3e2; border-radius: 0.5rem; display: inline-block;">
                <span style="color: #ea580c; font-weight: 600; font-size: 0.875rem;">Visual</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3 class="feature-title">Automated Workflows</h3>
            <p class="feature-description">
                Eliminate manual processes with intelligent automation that learns and adapts.
            </p>
            <div style="margin-top: 1rem; padding: 0.5rem 1rem; background: #ecfdf5; border-radius: 0.5rem; display: inline-block;">
                <span style="color: #059669; font-weight: 600; font-size: 0.875rem;">Efficient</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Trust Indicators
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0; padding: 2rem; background: rgba(255,255,255,0.8); border-radius: 1rem;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 0.5rem; color: #64748b;">
                <span>🛡️</span> Enterprise Security
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem; color: #64748b;">
                <span>🌍</span> Global Scale
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA Section
    st.markdown("""
    <div class="cta-section">
        <h2 class="cta-title">
            Ready to Build Your<br>
            <span style="color: var(--primary-cyan);">Second Brain?</span>
        </h2>
        <p class="cta-subtitle">
            Join forward-thinking businesses that have eliminated manual decision-making. 
            Start optimizing your operations with AI today.
        </p>
        <div class="hero-buttons">
            <a href="#" class="btn btn-primary">Start Free Trial →</a>
            <a href="#" class="btn btn-secondary">Schedule Demo</a>
        </div>
        <div class="cta-features">
            <div class="cta-feature">
                <span>❄️</span> 14-day free trial
            </div>
            <div class="cta-feature">
                <span>❄️</span> No credit card required
            </div>
            <div class="cta-feature">
                <span>❄️</span> Setup in minutes
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
