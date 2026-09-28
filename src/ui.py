import streamlit as st

def inject_css():
    st.markdown("""
    <style>
    .main .block-container {max-width: 1250px; padding-top: 1.5rem;}
    .hero {
        padding: 2rem; border-radius: 22px; margin-bottom: 1rem;
        background: linear-gradient(135deg,#0f172a,#1e3a8a);
        color: white;
    }
    .hero h1 {font-size: 2.4rem; margin-bottom: .35rem;}
    .vehicle-card {
        padding: 1rem; border: 1px solid #e2e8f0; border-radius: 18px;
        background: white; min-height: 250px;
        box-shadow: 0 4px 18px rgba(15,23,42,.06);
    }
    .price {font-size: 1.45rem; font-weight: 800;}
    .muted {color:#64748b;}
    .badge {
        display:inline-block; padding:.25rem .6rem; border-radius:999px;
        background:#dbeafe; color:#1d4ed8; font-size:.8rem; font-weight:700;
    }
    </style>
    """, unsafe_allow_html=True)

def hero():
    st.markdown("""
    <div class="hero">
      <h1>🚗 Vehicle Rental Platform</h1>
      <p>Discover, compare and book vehicles with transparent pricing and real-time availability.</p>
    </div>
    """, unsafe_allow_html=True)

def metric_card(label, value, help_text=""):
    st.metric(label, value, help=help_text)
