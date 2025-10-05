# home_page.py
import streamlit as st

BASE_CSS = """
<style>
:root{
  --bg: #0b1020;
  --card:#0f172a;
  --muted:#94a3b8;
  --text:#e2e8f0;
  --primary:#0ea5e9;           /* cyan-500 */
  --primary-600:#0284c7;        /* cyan-600 */
  --ring: rgba(14,165,233,.35);
  --gray-800:#1f2937;
  --gray-600:#4b5563;
  --white:#ffffff;
  --primary-cyan:#22d3ee;
}

/* App background */
html, body, .stApp { background: var(--bg); }

/* Layout helpers */
.container { max-width: 1100px; margin: 0 auto; padding: 0 20px; }
.page-header { text-align: center; }

/* Hero */
.hero-section { padding: 4rem 0 2rem; text-align: center; color: var(--text); }
.hero-title { font-size: clamp(2.2rem, 6vw, 4rem); font-weight: 800; line-height: 1.1; letter-spacing: -0.02em; }
.hero-subtitle { margin: 1rem auto 1.75rem; max-width: 800px; font-size: 1.1rem; color: rgba(226,232,240,.85); }
.hero-buttons { display: inline-flex; gap: .75rem; flex-wrap: wrap; }

/* Buttons */
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: .75rem 1rem; border-radius: .75rem; font-weight: 600;
  border: 1px solid transparent; text-decoration: none; cursor: pointer;
  transition: transform .05s ease, box-shadow .15s ease, background .15s ease, color .15s ease, border-color .15s ease;
}
.btn:focus { outline: none; box-shadow: 0 0 0 4px var(--ring); }
.btn-primary { background: var(--white); color: var(--primary); border-color: rgba(255,255,255,.2); }
.btn-primary:hover { background: #f8fafc; transform: translateY(-1px); }
.btn-secondary { background: transparent; color: var(--white); border-color: rgba(255,255,255,.35); }
.btn-secondary:hover { border-color: rgba(255,255,255,.6); transform: translateY(-1px); }

/* Features */
.feature-card {
  background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 1rem; padding: 1.25rem;
  color: var(--text);
  height: 100%;
  box-shadow: 0 6px 24px rgba(2,8,23,0.25);
}
.feature-card:hover { border-color: rgba(56,189,248,.35); }
.feature-icon { font-size: 1.5rem; }
.feature-title { margin: .25rem 0 .25rem; }
.feature-description { color: rgba(226,232,240,.75); font-size: .98rem; }
.badge { margin-top: .75rem; display:inline-block; padding:.4rem .7rem; border-radius:.5rem; font-weight:600; font-size:.85rem; }
.badge-core { background:#f0f9ff; color:#0ea5e9; }
.badge-pop { background:#fef3c7; color:#d97706; }
.badge-247 { background:#f0fdf4; color:#16a34a; }
.badge-smart { background:#f3e8ff; color:#7c3aed; }
.badge-visual { background:#fef3e2; color:#ea580c; }
.badge-eff { background:#ecfdf5; color:#059669; }

/* Trust & CTA */
.trust {
  text-align:center; margin: 2.5rem 0; padding: 1.25rem;
  background: rgba(255,255,255,.06); border-radius: 1rem;
  border: 1px solid rgba(255,255,255,.08);
  color: #cbd5e1;
}
.cta-section { text-align:center; padding: 3rem 0 4rem; color: var(--text); }
.cta-title { font-size: clamp(1.8rem, 4vw, 3rem); font-weight: 800; }
.cta-subtitle { color: rgba(226,232,240,.8); max-width: 800px; margin: .75rem auto 1.5rem; }

/* Responsive grid helper (Streamlit columns handle layout; this helps card spacing on narrow widths) */
.card-grid { display: grid; gap: 1rem; }
@media (min-width: 900px) { .card-grid { grid-template-columns: repeat(3, 1fr); } }

/* Utility */
.cta-feature { display:inline-flex; gap:.5rem; align-items:center; color: rgba(255,255,255,0.85); }
</style>
"""

def render_home_page():
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    st.markdown('<div class="container">', unsafe_allow_html=True)

    # -------- HERO --------
    st.markdown(
        """
        <section class="hero-section">
          <h1 class="hero-title">
            Your Business<br><span style="color:#38bdf8;">Optimization</span><br>Engine
          </h1>
          <p class="hero-subtitle">
            Skip the prescriptive processes. Let AI make intelligent decisions for your business.
            From inventory optimization to operational efficiency — your second brain handles it all.
          </p>
          <div class="hero-buttons" role="group" aria-label="Primary actions">
            <a href="https://example.com/start" class="btn btn-primary" aria-label="Get Started Today">Get Started Today →</a>
            <a href="https://example.com/demo" class="btn btn-secondary" aria-label="Schedule a Demo">Schedule Demo</a>
          </div>
          <div style="margin-top:1.5rem; display:flex; justify-content:center; gap:1.25rem; flex-wrap:wrap;">
            <div class="cta-feature"><span aria-hidden="true">❄️</span> 14-day free trial</div>
            <div class="cta-feature"><span aria-hidden="true">🔐</span> No credit card required</div>
            <div class="cta-feature"><span aria-hidden="true">⚙️</span> Setup in minutes</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True
    )

    # -------- FEATURES HEADER --------
    st.markdown(
        """
        <div class="page-header" style="margin-top:2.25rem;">
          <h2 style="color:var(--text); font-size:2rem; font-weight:800;">
            Intelligent Business <span style="color: var(--primary-cyan);">Automation</span>
          </h2>
          <p style="color:rgba(226,232,240,.8); font-size:1.05rem; max-width:800px; margin: .5rem auto 0;">
            Replace manual decision-making with AI-powered intelligence. See how Second Brain transforms businesses across industries.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------- FEATURE CARDS --------
    # Use Streamlit columns for robust responsiveness; card styles ensure equal look.
    with st.container():
        cols_top = st.columns(3, gap="large")
        with cols_top[0]:
            st.markdown("""
            <div class="feature-card">
              <div class="feature-icon">🎯</div>
              <h3 class="feature-title">AI-Powered Decision Making</h3>
              <p class="feature-description">
                Advanced algorithms analyze your business patterns and make optimal decisions automatically.
              </p>
              <span class="badge badge-core">Core Feature</span>
            </div>
            """, unsafe_allow_html=True)
        with cols_top[1]:
            st.markdown("""
            <div class="feature-card">
              <div class="feature-icon">📈</div>
              <h3 class="feature-title">Inventory Optimization</h3>
              <p class="feature-description">
                Know exactly when to order, how much to order, and in what combinations for maximum efficiency.
              </p>
              <span class="badge badge-pop">Popular</span>
            </div>
            """, unsafe_allow_html=True)
        with cols_top[2]:
            st.markdown("""
            <div class="feature-card">
              <div class="feature-icon">⏰</div>
              <h3 class="feature-title">Real-Time Monitoring</h3>
              <p class="feature-description">
                Continuous tracking of your business metrics with instant alerts when action is needed.
              </p>
              <span class="badge badge-247">24/7</span>
            </div>
            """, unsafe_allow_html=True)

        cols_bottom = st.columns(3, gap="large")
        with cols_bottom[0]:
            st.markdown("""
            <div class="feature-card">
              <div class="feature-icon">🔮</div>
              <h3 class="feature-title">Predictive Analytics</h3>
              <p class="feature-description">
                Forecast demand, identify trends, and prepare for market changes before they happen.
              </p>
              <span class="badge badge-smart">Smart</span>
            </div>
            """, unsafe_allow_html=True)
        with cols_bottom[1]:
            st.markdown("""
            <div class="feature-card">
              <div class="feature-icon">📊</div>
              <h3 class="feature-title">Business Intelligence</h3>
              <p class="feature-description">
                Transform raw data into actionable insights with beautiful, intuitive dashboards.
              </p>
              <span class="badge badge-visual">Visual</span>
            </div>
            """, unsafe_allow_html=True)
        with cols_bottom[2]:
            st.markdown("""
            <div class="feature-card">
              <div class="feature-icon">⚡</div>
              <h3 class="feature-title">Automated Workflows</h3>
              <p class="feature-description">
                Eliminate manual processes with intelligent automation that learns and adapts.
              </p>
              <span class="badge badge-eff">Efficient</span>
            </div>
            """, unsafe_allow_html=True)

    # -------- TRUST STRIP --------
    st.markdown("""
    <div class="trust" role="status" aria-live="polite">
      <div style="display:flex; justify-content:center; align-items:center; gap:1.25rem; flex-wrap:wrap;">
        <div style="display:flex; align-items:center; gap:.5rem;"><span aria-hidden="true">🛡️</span> Enterprise Security</div>
        <div style="display:flex; align-items:center; gap:.5rem;"><span aria-hidden="true">🌍</span> Global Scale</div>
        <div style="display:flex; align-items:center; gap:.5rem;"><span aria-hidden="true">⚡</span> Fast Integration</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # -------- CTA --------
    st.markdown(
        """
        <section class="cta-section">
          <h2 class="cta-title">Ready to Build Your<br><span style="color: var(--primary-cyan);">Second Brain?</span></h2>
          <p class="cta-subtitle">
            Join forward-thinking businesses that have eliminated manual decision-making.
            Start optimizing your operations with AI today.
          </p>
          <div class="hero-buttons">
            <a href="https://example.com/start" class="btn btn-primary" aria-label="Start Free Trial">Start Free Trial →</a>
            <a href="https://example.com/demo" class="btn btn-secondary" aria-label="Schedule a Demo">Schedule Demo</a>
          </div>
        </section>
        """,
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)
