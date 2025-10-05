# template.py
import streamlit as st


def inject_global_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Root Variables - SecondBrain Color Scheme */
    :root {
        /* Colors from screenshots */
        --primary-cyan: #1DB7E8;
        --primary-blue: #0EA5E9;
        --dark-blue: #1e293b;
        --light-blue: #38bdf8;
        --gradient-start: #0ea5e9;
        --gradient-end: #06b6d4;

        /* Neutrals */
        --white: #ffffff;
        --gray-50: #f8fafc;
        --gray-100: #f1f5f9;
        --gray-200: #e2e8f0;
        --gray-300: #cbd5e1;
        --gray-400: #94a3b8;
        --gray-500: #64748b;
        --gray-600: #475569;
        --gray-700: #334155;
        --gray-800: #1e293b;
        --gray-900: #0f172a;

        /* Semantic Colors */
        --success: #22c55e;
        --warning: #f59e0b;
        --error: #ef4444;
        --info: var(--primary-cyan);

        /* Spacing */
        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
        --spacing-2xl: 3rem;

        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

        /* Border Radius */
        --radius-sm: 0.375rem;
        --radius-md: 0.5rem;
        --radius-lg: 0.75rem;
        --radius-xl: 1rem;
        --radius-2xl: 1.5rem;
    }

    /* Base Styles */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        background: var(--gray-50);
        color: var(--gray-800);
        line-height: 1.6;
    }

    /* Hide Streamlit Elements */
    .stAppHeader, .stAppToolbar, .stDecoration, .stStatusWidget {
        display: none !important;
    }

    /* Main App Container */
    .stApp {
        background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
        min-height: 100vh;
    }

    /* Remove default Streamlit padding */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Page Container */
    .page-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: var(--spacing-xl);
        min-height: 100vh;
    }

    /* Navigation Styles */
    .nav-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--spacing-md) var(--spacing-xl);
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--gray-200);
        margin-bottom: var(--spacing-xl);
    }

    .nav-brand {
        display: flex;
        align-items: center;
        gap: var(--spacing-sm);
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--gray-800);
    }

    .brand-icon {
        font-size: 2rem;
    }

    .nav-tabs {
        display: flex;
        gap: var(--spacing-sm);
    }

    .nav-tab {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        padding: var(--spacing-sm) var(--spacing-md);
        border-radius: var(--radius-lg);
        color: var(--gray-600);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .nav-tab:hover {
        background: var(--gray-100);
        color: var(--gray-800);
    }

    .nav-tab.active {
        background: var(--primary-cyan);
        color: var(--white);
    }

    .nav-actions {
        display: flex;
        gap: var(--spacing-sm);
    }

    .nav-action {
        padding: var(--spacing-sm);
        border-radius: var(--radius-md);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .nav-action:hover {
        background: var(--gray-100);
    }

    /* Page Headers */
    .page-header {
        text-align: center;
        margin-bottom: var(--spacing-2xl);
    }

    .page-title {
        font-size: 3rem;
        font-weight: 800;
        color: var(--white);
        margin-bottom: var(--spacing-md);
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .page-subtitle {
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.9);
        max-width: 600px;
        margin: 0 auto;
    }

    /* Card Styles */
    .card {
        background: var(--white);
        border-radius: var(--radius-xl);
        padding: var(--spacing-xl);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--gray-200);
        margin-bottom: var(--spacing-lg);
        transition: all 0.3s ease;
    }

    .card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-xl);
    }

    .card-header {
        margin-bottom: var(--spacing-lg);
    }

    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--gray-800);
        margin-bottom: var(--spacing-xs);
    }

    .card-subtitle {
        color: var(--gray-500);
        font-size: 0.875rem;
    }

    /* Feature Cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: var(--spacing-xl);
        margin: var(--spacing-2xl) 0;
    }

    .feature-card {
        background: var(--white);
        border-radius: var(--radius-xl);
        padding: var(--spacing-xl);
        text-align: center;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
        border: 1px solid var(--gray-200);
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-xl);
        border-color: var(--primary-cyan);
    }

    .feature-icon {
        font-size: 3rem;
        margin-bottom: var(--spacing-lg);
        color: var(--primary-cyan);
    }

    .feature-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--gray-800);
        margin-bottom: var(--spacing-md);
    }

    .feature-description {
        color: var(--gray-600);
        line-height: 1.6;
    }

    /* Buttons */
    .btn {
        display: inline-flex;
        align-items: center;
        gap: var(--spacing-xs);
        padding: var(--spacing-md) var(--spacing-xl);
        border-radius: var(--radius-lg);
        font-weight: 600;
        text-decoration: none;
        transition: all 0.2s ease;
        cursor: pointer;
        border: none;
        font-size: 1rem;
    }

    .btn-primary {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        color: var(--white);
        box-shadow: var(--shadow-md);
    }

    .btn-primary:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-lg);
    }

    .btn-secondary {
        background: var(--white);
        color: var(--gray-700);
        border: 2px solid var(--gray-200);
    }

    .btn-secondary:hover {
        border-color: var(--primary-cyan);
        color: var(--primary-cyan);
    }

    /* Metrics */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: var(--spacing-lg);
        margin-bottom: var(--spacing-2xl);
    }

    .metric-card {
        background: var(--white);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-md);
        border-left: 4px solid var(--primary-cyan);
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--gray-500);
        margin-bottom: var(--spacing-xs);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--gray-800);
        margin-bottom: var(--spacing-xs);
    }

    .metric-change {
        font-size: 0.875rem;
        font-weight: 500;
    }

    .metric-change.positive {
        color: var(--success);
    }

    .metric-change.negative {
        color: var(--error);
    }

    /* Charts and Plots */
    div[data-testid="stPlotlyChart"] {
        background: var(--white);
        border-radius: var(--radius-lg);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--gray-200);
        margin-bottom: var(--spacing-lg);
    }

    /* DataFrames */
    div[data-testid="stDataFrame"] {
        background: var(--white);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
        border: 1px solid var(--gray-200);
        overflow: hidden;
    }

    /* Info/Warning/Success Messages */
    div[data-baseweb="notification"] {
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
    }

    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: var(--spacing-2xl) 0;
        background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
        color: var(--white);
        border-radius: var(--radius-2xl);
        margin-bottom: var(--spacing-2xl);
    }

    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: var(--spacing-lg);
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .hero-subtitle {
        font-size: 1.5rem;
        margin-bottom: var(--spacing-2xl);
        opacity: 0.9;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }

    .hero-buttons {
        display: flex;
        justify-content: center;
        gap: var(--spacing-lg);
        flex-wrap: wrap;
    }

    /* CTA Section */
    .cta-section {
        background: var(--white);
        border-radius: var(--radius-2xl);
        padding: var(--spacing-2xl);
        text-align: center;
        box-shadow: var(--shadow-lg);
        margin: var(--spacing-2xl) 0;
    }

    .cta-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--gray-800);
        margin-bottom: var(--spacing-lg);
    }

    .cta-subtitle {
        font-size: 1.1rem;
        color: var(--gray-600);
        margin-bottom: var(--spacing-2xl);
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }

    .cta-features {
        display: flex;
        justify-content: center;
        gap: var(--spacing-xl);
        margin-top: var(--spacing-xl);
        flex-wrap: wrap;
    }

    .cta-feature {
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
        color: var(--gray-600);
        font-size: 0.875rem;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .page-container {
            padding: var(--spacing-md);
        }

        .page-title {
            font-size: 2rem;
        }

        .hero-title {
            font-size: 2.5rem;
        }

        .hero-subtitle {
            font-size: 1.2rem;
        }

        .feature-grid {
            grid-template-columns: 1fr;
        }

        .metrics-grid {
            grid-template-columns: 1fr;
        }

        .nav-container {
            flex-direction: column;
            gap: var(--spacing-md);
        }

        .hero-buttons {
            flex-direction: column;
            align-items: center;
        }
    }

    /* Streamlit Button Overrides */
    .stButton button {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        color: var(--white);
        border: none;
        border-radius: var(--radius-lg);
        padding: var(--spacing-md) var(--spacing-xl);
        font-weight: 600;
        box-shadow: var(--shadow-md);
        transition: all 0.2s ease;
    }

    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-lg);
        filter: brightness(1.05);
    }

    /* Sidebar Styles */
    .css-1d391kg {
        background: var(--white);
    }

    .css-1d391kg .css-17eq0hr {
        background: var(--white);
    }
    </style>
    """, unsafe_allow_html=True)
