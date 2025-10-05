# home_page.py
import streamlit as st
import base64
from pathlib import Path


def render_home_page():
    # --- Load assets from assets folder ---
    assets_dir = Path(__file__).parent / "assets"
    logo_path = assets_dir / "brain.svg"
    demo_path = assets_dir / "Demo.jpg"

    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    demo_b64 = base64.b64encode(demo_path.read_bytes()).decode("utf-8")

    # --- CSS for transparent hero container ---
    st.markdown("""
    <style>
      /* Transparent hero container */
      .hero-transparent {
        background: transparent;
        border: none;
        padding: 4rem 2rem 3rem;
        border-radius: 0;
        color: #fff;
        position: relative;
        overflow: hidden;
      }

      .hero-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        flex-wrap: wrap;
        background: transparent;
      }

      .hero-left {
        flex: 1 1 50%;
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
        background:transparent;
        color:#fff;
        border-color:rgba(255,255,255,.5);
      }

      .btn-primary:hover { background:#f0f9ff; }
      .btn-secondary:hover { border-color:#fff; }

      .mini-feats {
        display:flex;
        gap:1.25rem;
        flex-wrap:wrap;
        color: rgba(255,255,255,0.9);
        font-size: 0.95rem;
        background: transparent;
      }

      .hero-right {
        flex: 1 1 45%;
        min-width: 300px;
        position: relative;
        text-align: right;
        background: transparent;
      }

      .hero-right img {
        max-width: 100%;
        border-radius: 1rem;
        box-shadow: 0 12px 40px rgba(0,0,0,0.35);
      }

      /* Remove Streamlit’s default background color around markdown blocks */
      section[data-testid="stMarkdownContainer"] {
        background: transparent !important;
      }
    </style>
    """, unsafe_allow_html=True)

    # --- HERO SECTION (transparent container) ---
    st.markdown(f"""
    <div class="hero-transparent">
      <div class="hero-container">
        <div class="hero-left">
          <div class="brand">
            <img src="data:image/svg+xml;base64,{logo_b64}" alt="Second Brain logo" />
            <div class="name">Second Brain</div>
          </div>
          <div class="hero-title">
            Your Business<br>Optimization<br>Engine
          </div>
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
    """, unsafe_allow_html=True)

    # ---- Keep your existing features, trust, CTA, etc. below ----
