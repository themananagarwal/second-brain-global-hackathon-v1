# home_page.py
import streamlit as st
import base64
from pathlib import Path

def _b64(path: Path) -> str:
    """Read a file and return base64-encoded string. Works for svg/jpg/png."""
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")

def _find_asset(name: str) -> Path:
    """Search in current dir and ./assets for the given filename."""
    here = Path(__file__).parent
    p1 = here / name
    p2 = here / "assets" / name
    if p1.exists():
        return p1
    if p2.exists():
        return p2
    raise FileNotFoundError(f"Could not find {name}. Put it next to home_page.py or in ./assets/")

def render_home_page():
    # ---- Load your assets ----
    logo_path = _find_asset("brain.svg")
    demo_path = _find_asset("demo.jpg")
    logo_b64 = _b64(logo_path)     # inline embed (reliable in Streamlit HTML)
    demo_b64 = _b64(demo_path)

    # ---- Minimal CSS for brand row + split hero like your screenshot ----
    st.markdown("""
    <style>
      .hero-wrap { max-width: 1200px; margin: 0 auto; padding: 2rem 1rem 0; }
      .brand { display:flex; align-items:center; gap:.6rem; margin-bottom:1.25rem; }
      .brand img { width:28px; height:28px; vertical-align:middle;
                   /* force white logo even if original isn't white */
                   filter: brightness(0) invert(1); }
      .brand .name { font-weight: 700; color: #fff; font-size: 1.05rem; }

      .hero-flex { display:flex; gap:2rem; align-items:center; flex-wrap:wrap; }
      .hero-left { flex:1 1 460px; min-width: 320px; }
      .hero-right { flex:1 1 520px; min-width: 320px; display:flex; justify-content:center; }
      .hero-right img { width:100%; height:auto; border-radius: 1rem; box-shadow: 0 16px 48px rgba(3, 7, 18, 0.35); }

      .hero-section { padding: 1.25rem 0 0; color: white; }
      .hero-title { font-size: clamp(2.2rem, 6vw, 4.25rem); font-weight: 800; line-height: 1.05; letter-spacing:-.02em; }
      .hero-subtitle { margin: 1rem 0 1.5rem; color: rgba(255,255,255,.9); font-size: 1.05rem; }

      .hero-buttons { display:flex; gap: .75rem; flex-wrap: wrap; }
      .btn { display:inline-flex; padding:.8rem 1.1rem; border-radius:.75rem; font-weight:700; text-decoration:none; border:1px solid transparent; }
      .btn.btn-primary { background:#fff; color:#0ea5e9; }
      .btn.btn-secondary { background:transparent; color:#fff; border-color:rgba(255,255,255,.45); }

      /* optional: small feature line below buttons */
      .mini-feats { display:flex; gap:1.25rem; flex-wrap:wrap; margin-top:1rem; color: rgba(255,255,255,0.85); }
      .mini-feats span { display:inline-flex; align-items:center; gap:.5rem; }
    </style>
    """, unsafe_allow_html=True)

    # ---- Brand + Split Hero (logo + name on top-left, big title, demo image on right) ----
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
              <a href="#" class="btn btn-secondary">Schedule Demo</a>
            </div>
            <div class="mini-feats">
              <span>📊 Real-time Analytics</span>
              <span>⚡ Instant Optimization</span>
            </div>
          </div>
        </div>

        <div class="hero-right">
          <img src="data:image/jpeg;base64,{demo_b64}" alt="Product demo" />
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- (Keep the rest of your sections below as-is) ----
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

    # ... your feature cards, trust indicators, and CTA sections unchanged ...
