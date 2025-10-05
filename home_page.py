# home_page.py
import streamlit as st
import base64
from pathlib import Path


def render_home_page():
    # --- Load assets from the assets folder ---
    assets_dir = Path(__file__).parent / "assets"
    logo_path = assets_dir / "brain.svg"
    demo_path = assets_dir / "Demo.jpg"

    # Read and encode both images in base64 so they can render inline
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    demo_b64 = base64.b64encode(demo_path.read_bytes()).decode("utf-8")

    # --- CSS for the split hero section ---
    st.markdown("""
    <style>
      .hero-wrap { max-width: 1200px; margin: 0 auto; padding: 3rem 1rem 0; }
      .brand { display:flex; align-items:center; gap:.6rem; margin-bottom:1.25rem; }
      .brand img { width:32px; height:32px; vertical-align:middle;
                   filter: brightness(0) invert(1); } /* makes SVG white */
      .brand .name { font-weight: 700; color: #fff; font-size: 1.15rem; }

      .hero-flex { display:flex; gap:2.5rem; align-items:center; flex-wrap:wrap; }
      .hero-left { flex:1 1 460px; min-width: 320px; }
      .hero-right { flex:1 1 520px; min-width: 320px; display:flex; justify-content:center; }
      .hero-right img { width:100%; height:auto; border-radius: 1rem; box-shadow: 0 16px 48px rgba(3, 7, 18, 0.35); }

      .hero-section { padding: 1rem 0 0; color: white; }
      .hero-title { font-size: clamp(2.4rem, 6vw, 4.5rem); font-weight: 800; line-height: 1.05; letter-spacing:-.02em; }
      .hero-subtitle { margin: 1rem 0 1.5rem; color: rgba(255,255,255,.9); font-size: 1.05rem; }

      .hero-buttons { display:flex; gap: .75rem; flex-wrap: wrap; }
      .btn { display:inline-flex; padding:.8rem 1.1rem; border-radius:.75rem; font-weight:700; text-decoration:none; border:1px solid transparent; }
      .btn.btn-primary { background:#fff; color:#0ea5e9; }
      .btn.btn-secondary { background:transparent; color:#fff; border-color:rgba(255,255,255,.45); }
      .btn.btn-primary:hover { background:#f0f9ff; }
      .btn.btn-secondary:hover { border-color:#fff; }

      .mini-feats { display:flex; gap:1.25rem; flex-wrap:wrap; margin-top:1.25rem; color: rgba(255,255,255,0.85); }
      .mini-feats span { display:inline-flex; align-items:center; gap:.5rem; font-size:.95rem; }
    </style>
    """, unsafe_allow_html=True)

    # --- HERO SECTION (logo + name + headline + right image) ---
    st.markdown(f"""
    <div class="hero-wrap">
      <div class="brand">
        <img src="data:image/svg+xml;base64,{logo_b64}" alt="Second Brain logo" />
        <div class="name">Second Brain</div>
      </div>

      <div class="hero-flex">
        <div class="hero-left">
          <div class="hero-section">
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
        </div>

        <div class="hero-right">
          <img src="data:image/jpeg;base64,{demo_b64}" alt="Dashboard demo" />
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Keep your existing sections below ----
    # (Feature cards, trust indicators, CTA, etc.)
