# template.py
import streamlit as st


def inject_global_css():
    """
    Inject comprehensive global CSS with exact design specifications
    Primary Gradient: #00BFFF → #0099E5
    8px grid system, precise typography scale, semantic colors
    """
    st.markdown("""
    <style>
    /* ========================= */
    /* CSS RESET & BASE STYLES */
    /* ========================= */

    /* Hide Streamlit Chrome */
    #MainMenu {visibility: hidden;}
    .stAppHeader {display: none;}
    .stDecoration {display: none;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* App/Page background */
    html, body, .stApp {
        background-color: #F8F9FA;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }

    /* ========================= */
    /* CSS VARIABLES */
    /* ========================= */

    :root {
        /* Primary Colors */
        --color-primary-start: #00BFFF;
        --color-primary-end: #0099E5;
        --color-gradient: linear-gradient(135deg, #00BFFF 0%, #0099E5 100%);

        /* Neutral Colors */
        --color-white: #FFFFFF;
        --color-background: #F8F9FA;
        --color-text-primary: #2C3E50;
        --color-text-light: #6C757D;
        --color-border: #E5E7EB;

        /* Semantic Colors */
        --color-success: #28A745;
        --color-warning: #FF9500;
        --color-error: #DC3545;

        /* Chart Colors */
        --color-chart-text: #374151;
        --color-chart-grid: rgba(148, 163, 184, 0.1);

        /* Spacing (8px grid) */
        --spacing-xs: 8px;
        --spacing-sm: 16px;
        --spacing-md: 24px;
        --spacing-lg: 32px;
        --spacing-xl: 48px;

        /* Border Radius */
        --radius-card: 8px;
        --radius-button: 6px;

        /* Shadows */
        --shadow-card: 0px 2px 8px rgba(0, 0, 0, 0.1);
        --shadow-hover: 0px 4px 12px rgba(0, 0, 0, 0.15);

        /* Typography */
        --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;

        /* HERO background hook (default = gradient) */
        --hero-background: var(--color-gradient);
    }

    /* ========================= */
    /* TYPOGRAPHY */
    /* ========================= */

    body {
        font-family: var(--font-family);
        font-size: 1rem;
        color: var(--color-text-primary);
        line-height: 1.6;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-family);
        font-weight: 600;
        color: var(--color-text-primary);
        margin: 0 0 var(--spacing-sm) 0;
    }

    h1 {
        font-size: 4rem;
        font-weight: 800;
        line-height: 1.1;
    }

    h2 {
        font-size: 2rem;
        font-weight: 700;
    }

    h3 {
        font-size: 1.5rem;
        font-weight: 600;
    }

    p {
        margin: 0 0 var(--spacing-sm) 0;
        color: var(--color-text-primary);
    }

    /* ========================= */
    /* BUTTON STYLES */
    /* ========================= */

    /* Primary Button (Gradient) */
    .stButton > button[kind="primary"],
    .stButton > button[data-baseweb="button"][kind="primary"] {
        background: var(--color-gradient) !important;
        color: var(--color-white) !important;
        border: none !important;
        border-radius: var(--radius-button) !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-baseweb="button"][kind="primary"]:hover {
        filter: brightness(1.1) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0px 4px 12px rgba(0, 191, 255, 0.3) !important;
    }

    .stButton > button[kind="primary"]:active {
        transform: translateY(0px) !important;
    }

    /* Secondary Button (White/Transparent) */
    .stButton > button[kind="secondary"],
    .stButton > button[data-baseweb="button"][kind="secondary"] {
        background: var(--color-white) !important;
        color: var(--color-text-light) !important;
        border: 1px solid var(--color-border) !important;
        border-radius: var(--radius-button) !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-baseweb="button"][kind="secondary"]:hover {
        background: var(--color-background) !important;
        border-color: var(--color-primary-start) !important;
        color: var(--color-text-primary) !important;
    }

    /* Navigation Buttons */
    .nav-button-active {
        background: var(--color-gradient) !important;
        color: var(--color-white) !important;
        border: none !important;
    }

    .nav-button-inactive {
        background: var(--color-white) !important;
        color: var(--color-text-light) !important;
        border: 1px solid var(--color-border) !important;
    }

    .nav-button-inactive:hover {
        background: var(--color-background) !important;
    }

    /* ========================= */
    /* CARD STYLES */
    /* ========================= */

    .card {
        background: var(--color-white);
        border-radius: var(--radius-card);
        padding: var(--spacing-sm);
        box-shadow: var(--shadow-card);
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }

    .card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
    }

    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--color-text-primary);
        margin-bottom: var(--spacing-sm);
    }

    .card-description {
        font-size: 1rem;
        color: var(--color-text-light);
        line-height: 1.6;
    }

    /* Feature Cards */
    .feature-card {
        background: var(--color-white);
        border-radius: var(--radius-card);
        padding: var(--spacing-md);
        box-shadow: var(--shadow-card);
        transition: all 0.3s ease;
        height: 100%;
        border: 1px solid var(--color-border);
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
        border-color: var(--color-primary-start);
    }

    .feature-icon {
        font-size: 3rem;
        margin-bottom: var(--spacing-sm);
        color: var(--color-primary-start);
    }

    /* ========================= */
    /* METRIC CARDS */
    /* ========================= */

    .metric-card {
        background: var(--color-white);
        border-radius: var(--radius-card);
        padding: var(--spacing-md);
        box-shadow: var(--shadow-card);
        border-left: 4px solid var(--color-primary-start);
        transition: all 0.2s ease;
    }

    .metric-card:hover {
        box-shadow: var(--shadow-hover);
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--color-text-light);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: var(--spacing-xs);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--color-text-primary);
        margin-bottom: var(--spacing-xs);
    }

    .metric-change {
        font-size: 0.875rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .metric-change.positive {
        color: var(--color-success);
    }

    .metric-change.negative {
        color: var(--color-error);
    }

    .metric-change.neutral {
        color: var(--color-text-light);
    }

    /* ========================= */
    /* NAVIGATION BAR */
    /* ========================= */

    .nav-container {
        background: var(--color-white);
        border-bottom: 1px solid var(--color-border);
        padding: var(--spacing-sm) 0;
        margin-bottom: var(--spacing-lg);
    }

    .nav-brand {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--color-primary-start);
    }

    .nav-brand-icon {
        font-size: 1.5rem;
        color: var(--color-primary-start);
    }

    /* ========================= */
    /* HERO SECTION */
    /* ========================= */

    /* Default hero now uses a variable so you can override or set transparent via helper classes */
    .hero-section {
        background: var(--hero-background);
        border-radius: var(--radius-card);
        padding: var(--spacing-xl) var(--spacing-md);
        margin-bottom: var(--spacing-lg);
        text-align: center;
        color: var(--color-white);
    }

    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        color: var(--color-white);
        margin-bottom: var(--spacing-sm);
        line-height: 1.1;
    }

    .hero-subtitle {
        font-size: 1.25rem;
        color: rgba(255, 255, 255, 0.95);
        margin-bottom: var(--spacing-md);
        line-height: 1.6;
    }

    .hero-icon {
        font-size: 5rem;
        margin-bottom: var(--spacing-md);
        animation: float 3s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    /* Transparent hero helpers (scoped, won’t affect rest of page) */
    .hero-transparent,
    .hero-section.is-transparent,
    .hero-section--transparent {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        /* optionally: padding: 0 !important; */
        color: inherit;
    }

    /* ========================= */
    /* SECTION STYLES */
    /* ========================= */

    .section {
        margin-bottom: var(--spacing-lg);
    }

    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--color-text-primary);
        margin-bottom: var(--spacing-md);
        text-align: center;
    }

    .section-description {
        font-size: 1.125rem;
        color: var(--color-text-light);
        text-align: center;
        max-width: 600px;
        margin: 0 auto var(--spacing-lg) auto;
    }

    /* ========================= */
    /* STREAMLIT COMPONENT OVERRIDES */
    /* ========================= */

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--color-white);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-card);
        font-weight: 600;
        color: var(--color-text-primary);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: var(--spacing-sm);
        border-bottom: 1px solid var(--color-border);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-button);
        padding: 12px 24px;
        font-weight: 600;
        background: var(--color-white);
        color: var(--color-text-light);
        border: 1px solid var(--color-border);
    }

    .stTabs [aria-selected="true"] {
        background: var(--color-gradient);
        color: var(--color-white);
        border: none;
    }

    /* Select Box */
    .stSelectbox > div > div {
        border-radius: var(--radius-button);
        border: 1px solid var(--color-border);
    }

    /* Text Input */
    .stTextInput > div > div > input {
        border-radius: var(--radius-button);
        border: 1px solid var(--color-border);
        padding: 12px;
    }

    /* Dataframe */
    .dataframe {
        border-radius: var(--radius-card);
        overflow: hidden;
        box-shadow: var(--shadow-card);
    }

    /* ========================= */
    /* ALERT STYLES */
    /* ========================= */

    .stAlert {
        border-radius: var(--radius-card);
        padding: var(--spacing-sm);
        border-left: 4px solid;
    }

    .stSuccess {
        border-left-color: var(--color-success);
        background: rgba(40, 167, 69, 0.1);
    }

    .stWarning {
        border-left-color: var(--color-warning);
        background: rgba(255, 149, 0, 0.1);
    }

    .stError {
        border-left-color: var(--color-error);
        background: rgba(220, 53, 69, 0.1);
    }

    .stInfo {
        border-left-color: var(--color-primary-start);
        background: rgba(0, 191, 255, 0.1);
    }

    /* ========================= */
    /* CHART CONTAINER */
    /* ========================= */

    .chart-container {
        background: var(--color-white);
        border-radius: var(--radius-card);
        padding: var(--spacing-md);
        box-shadow: var(--shadow-card);
        margin-bottom: var(--spacing-md);
    }

    .chart-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--color-text-primary);
        margin-bottom: var(--spacing-sm);
    }

    /* ========================= */
    /* UTILITY CLASSES */
    /* ========================= */

    .text-center {
        text-align: center;
    }

    .text-gradient {
        background: var(--color-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .flex-center {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: var(--spacing-sm);
    }

    .mb-sm { margin-bottom: var(--spacing-sm); }
    .mb-md { margin-bottom: var(--spacing-md); }
    .mb-lg { margin-bottom: var(--spacing-lg); }

    .mt-sm { margin-top: var(--spacing-sm); }
    .mt-md { margin-top: var(--spacing-md); }
    .mt-lg { margin-top: var(--spacing-lg); }

    /* ========================= */
    /* RESPONSIVE DESIGN */
    /* ========================= */

    @media (max-width: 768px) {
        .hero-title { font-size: 2.5rem; }
        .hero-subtitle { font-size: 1rem; }
        .metric-value { font-size: 1.5rem; }
        .section-title { font-size: 1.5rem; }
        .card { padding: var(--spacing-sm); }
    }

    /* ========================= */
    /* ANIMATION UTILITIES */
    /* ========================= */

    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .slide-up {
        animation: slideUp 0.3s ease-out;
    }

    @keyframes slideUp {
        from { transform: translateY(10px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    /* ========================= */
    /* LOADING STATES */
    /* ========================= */

    .stSpinner > div {
        border-color: var(--color-primary-start) !important;
        border-right-color: transparent !important;
    }

    /* ========================= */
    /* PLOTLY CHART OVERRIDES */
    /* ========================= */

    .js-plotly-plot .plotly .modebar {
        background: transparent !important;
    }

    .js-plotly-plot .plotly .modebar-btn {
        color: var(--color-text-light) !important;
    }

    .js-plotly-plot .plotly .modebar-btn:hover {
        background: var(--color-background) !important;
    }

    </style>
    """, unsafe_allow_html=True)
