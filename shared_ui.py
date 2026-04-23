# shared_ui.py
import streamlit as st
from translations import LANG

def render_top_bar():
    """Renders the Language & Theme toggles in the top right and injects CSS."""
    # 1. Initialize states if they don't exist
    if 'lang' not in st.session_state: st.session_state.lang = 'EN'
    if 'ui_theme' not in st.session_state: st.session_state.ui_theme = '💻 Auto'

    # 2. Top Right Alignment using columns
    c1, c2, c3 = st.columns([7, 1.5, 1.5])
    
    with c2:
        st.session_state.lang = st.selectbox(
            "Language", 
            ["EN", "BN"], 
            index=["EN", "BN"].index(st.session_state.lang),
            label_visibility="collapsed"
        )
        
    with c3:
        st.session_state.ui_theme = st.selectbox(
            "Theme", 
            ["💻 Auto", "☀️ Light", "🌙 Dark"], 
            index=["💻 Auto", "☀️ Light", "🌙 Dark"].index(st.session_state.ui_theme),
            label_visibility="collapsed"
        )

    # 3. Inject the CSS for the current theme
    inject_custom_css(st.session_state.ui_theme)
    
    # 4. Return the active dictionary so the page can use it for text translation
    return LANG[st.session_state.lang]

def inject_custom_css(theme_choice):
    base_css = """
    <style>
        /* 1. FORCE Header and Sidebar Arrow to be visible and always in front */
        header { visibility: visible !important; background: transparent !important; z-index: 9999 !important; }
        [data-testid="collapsedControl"] { visibility: visible !important; display: flex !important; z-index: 10000 !important; }
        
        /* 2. Hide ONLY the right-side Streamlit defaults (Deploy button, hamburger menu) */
        #MainMenu { display: none !important; }
        [data-testid="stHeaderActionElements"] { display: none !important; }
        footer { visibility: hidden !important; }
        
        /* 3. Give the top a little breathing room so content doesn't cover the arrow */
        .block-container { padding-top: 3.5rem !important; } 
        
        /* Button & Metric Styling */
        .stButton>button { transition: all 0.3s ease-in-out; border-radius: 6px; font-weight: 600; }
        .stButton>button[data-testid="baseButton-primary"] { background-color: #059669 !important; color: white !important; border: none !important; }
        .stButton>button[data-testid="baseButton-primary"]:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(5, 150, 105, 0.4) !important; background-color: #047857 !important; }
        div[data-testid="metric-container"] { border-radius: 10px; border-left: 5px solid #059669 !important; padding: 5% 5% 5% 10%; }
    </style>
    """
    
    theme_css = ""
    if theme_choice == "🌙 Dark":
        theme_css = """<style>[data-testid="stAppViewContainer"] { background-color: #0F172A !important; color: #F8FAFC !important; } [data-testid="stSidebar"] { background-color: #1E293B !important; } div[data-testid="metric-container"] { background-color: #1E293B !important; border-color: #334155 !important; } .stMarkdown, h1, h2, h3, p, label { color: #F8FAFC !important; }</style>"""
    elif theme_choice == "☀️ Light":
        theme_css = """<style>[data-testid="stAppViewContainer"] { background-color: #F8FAFC !important; color: #0F172A !important; } [data-testid="stSidebar"] { background-color: #F1F5F9 !important; } div[data-testid="metric-container"] { background-color: #FFFFFF !important; border-color: #E2E8F0 !important; } .stMarkdown, h1, h2, h3, p, label { color: #0F172A !important; }</style>"""
        
    st.markdown(base_css + theme_css, unsafe_allow_html=True)
