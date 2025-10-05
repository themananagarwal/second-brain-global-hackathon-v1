import streamlit as st
import base64
from pathlib import Path
import textwrap


def render_home_page():
    # --- Load assets from assets folder ---
    assets_dir = Path(__file__).parent / "assets"
    logo_path = assets_dir / "brain.svg"
    demo_path = assets_dir / "Demo.jpg"

    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    demo_b64 = base64.b64encode(demo_path.read_bytes()).decode("utf-8")

    # --- CSS (transparent container, image right, text left) ---
    
    st.markdown("""
    /* or a gradient background site-wide */
    html, body, .stApp { 
        background: linear-gradient(180deg, #0b1020 0%, #0f172a 100%);
    }
    <style>
      .hero-transparent {
        background: transparent;
        border: none;
        padding: 4rem 2rem 3rem;
        color: #fff;
      }

      .hero-container {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2.5rem;
        flex-wrap: wrap;
        background: transparent;
      }

      .hero-left {
        flex: 1 1 48%;
        min-width: 320px;
        text-align: left;
        background: transparent;
      }

      .brand {
        display: flex;
        align-items: center;
        gap: .6rem;
        margin-bottom: 1.25rem;
        background: transparent;
      }

      .brand img {
        width: 32px;
        height: 32px;
        filter: brightness(0) invert(1);
      }

      .brand .name {
        font-weight: 700;
        color: #fff;
        font-size: 1.15rem;
      }

      .hero-title {
        font-size: clamp(2.4rem, 6vw, 4.5rem);
        font-weight: 800;
        line-height: 1.05;
        margin-bottom: 1rem;
        text-align: left;
        background: transparent;
      }

      .hero-subtitle {
        margin: 0 0 2rem;
        color: rgba(255,255,255,.9);
        font-size: 1.1rem;
        max-width: 500px;
        background: transparent;
      }

      .hero-buttons {
        display: flex;
        gap: .75rem;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
        background: transparent;
      }

      .btn {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding:.8rem 1.2rem;
        border-radius:.75rem;
        font-weight:700;
        text-decoration:none;
        border:1px solid transparent;
        transition: 0.2s;
      }

      .btn-primary {
        background:#fff;
        color:#0ea5e9;
      }

      .btn-secondary {
        background:#fff;
        color:#0ea5e9;
      }

      .btn-primary:hover { background:#f0f9ff; }
      .btn-secondary:hover { background:#f0f9ff; }

      .mini-feats {
        display:flex;
        gap:1.25rem;
        flex-wrap:wrap;
        color: rgba(255,255,255,0.9);
        font-size: 0.95rem;
        background: transparent;
      }

      .hero-right {
        flex: 1 1 46%;
        min-width: 300px;
        text-align: right;
        background: transparent;
      }

      .hero-right img {
        max-width: 100%;
        height: auto;
        border-radius: 1rem;
        box-shadow: 0 12px 40px rgba(0,0,0,0.35);
      }

      /* Buttons row BELOW the hero, left-aligned to same container */
    .hero-actions {
        max-width: 1200px;
        margin: 1.5rem auto 0;
        display: flex;
        gap: .75rem;
    }

    .btn {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding:.8rem 1.2rem;
        border-radius:.75rem;
        font-weight:700;
        text-decoration:none;
        border:1px solid transparent;
        transition: 0.2s;
    }

    .btn-primary { background:#fff; color:#0ea5e9; }
    .btn-secondary { background:#fff; color:#0ea5e9; }
    .btn-primary:hover, .btn-secondary:hover { background:#f0f9ff; }
    </style>
    """, unsafe_allow_html=True)


    # --- HERO SECTION ---
    html = f"""
<div class="hero-transparent">
  <div class="hero-container">
    <div class="hero-left">
      <div class="brand">
        <img src="data:image/svg+xml;base64,{logo_b64}" alt="Second Brain logo" />
        <div class="name">Second Brain</div>
      </div>
      <div class="hero-title">Your Business<br>Optimization<br>Engine</div>
      <div class="hero-subtitle">
        Skip the prescriptive processes. Let AI make intelligent decisions for your business.
        From inventory optimization to operational efficiency – your second brain handles it all.
      </div>
      <div class="hero-buttons">
        <a href="#" class="btn btn-primary">Get Started Today →</a>
        <a href="#" class="btn btn-secondary">Watch Demo</a>
      </div>
      <div class="mini-feats">
        <span>📊 Real-time Analytics</span>
        <span>⚡ Instant Optimization</span>
      </div>
    </div>

    <div class="hero-right">
      <img src="data:image/jpeg;base64,{demo_b64}" alt="Dashboard demo" />
    </div>
  </div>
</div>
"""
    st.markdown(textwrap.dedent(html), unsafe_allow_html=True)

    # --- Features Section ---
    st.markdown("""
    <div class="page-header" style="margin-top: 4rem;">
        <h2 style="color: var(--gray-800); font-size: 2.5rem; font-weight: 700;">
            Intelligent Business <span style="color: #ffffff;">Automation</span>
        </h2>
        <p style="color: var(--gray-600); font-size: 1.1rem; max-width: 800px; margin: 1rem auto;">
            Replace manual decision-making with AI-powered intelligence. See how Second Brain 
            transforms businesses across industries.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Feature Cards ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3 class="feature-title" style="color: #0ea5e9;">AI-Powered Decision Making</h3>
            <p class="feature-description">
                Advanced algorithms analyze your business patterns and make optimal decisions automatically.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <h3 class="feature-title" style="color: #0ea5e9;">Inventory Optimization</h3>
            <p class="feature-description">
                Know exactly when to order, how much to order, and in what combinations for maximum efficiency.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⏰</div>
            <h3 class="feature-title" style="color: #0ea5e9;">Real-Time Monitoring</h3>
            <p class="feature-description">
                Continuous tracking of your business metrics with instant alerts when action is needed.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- CTA Section ---
    st.markdown("""
    <div class="cta-section" style="margin-top: 4rem; text-align: center;">
        <h2 class="cta-title" style="font-size: 2.5rem; color: var(--gray-900); font-weight: 700;">
            Ready to Build Your<br>
            <span style="color: #0ea5e9;">Second Brain?</span>
        </h2>
        <p class="cta-subtitle" style="color: #475569; max-width: 700px; margin: 1rem auto;">
            Join forward-thinking businesses that have eliminated manual decision-making. 
            Start optimizing your operations with AI today.
        </p>
        <div class="hero-buttons" style="justify-content: center;">
            <a href="#" class="btn btn-primary">Start Free Trial →</a>
            <a href="#" class="btn btn-secondary">Schedule Demo</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
