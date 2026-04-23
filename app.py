# app.py
import streamlit as st
from database.schema import init_tables
from database.queries import verify_login
from config import APP_NAME
from shared_ui import render_top_bar # Import our new tool

init_tables()
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🚑")

# Call the top bar! This injects the CSS and returns the language dictionary
t = render_top_bar()

# --- INITIALIZE SECURE SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'role' not in st.session_state: st.session_state.role = None
if 'user_name' not in st.session_state: st.session_state.user_name = None
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'customer_phone' not in st.session_state: st.session_state.customer_phone = ''
if 'customer_name' not in st.session_state: st.session_state.customer_name = '' 

st.sidebar.title(t["sidebar_title"])

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in:
    st.sidebar.info(t["login_prompt"])
    login_type = st.sidebar.radio(t["portal"], ["Customer", "Driver", "Manager"])
    
    with st.sidebar.form("login_form"):
        identifier = st.text_input("Admin Username" if login_type == "Manager" else t["phone"])
        password = st.text_input(t["pass"], type="password")
        submit = st.form_submit_button(t["login_btn"], type="primary", use_container_width=True)
        
        if submit:
            success, user = verify_login(login_type, identifier, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.role = login_type.lower()
                
                if login_type == "Manager":
                    st.session_state.user_name = "System Admin"
                elif login_type == "Driver":
                    st.session_state.user_name = user['full_name']
                    st.session_state.user_id = user['id']
                elif login_type == "Customer":
                    st.session_state.user_name = user['full_name']
                    st.session_state.customer_name = user['full_name'] 
                    st.session_state.customer_phone = user['phone']
                    st.session_state.is_registered = 1
                
                st.sidebar.success(t["auth_success"])
                st.rerun()
            else:
                st.sidebar.error(t["invalid_cred"])
else:
    # --- LOGGED IN VIEW ---
    st.sidebar.success(f"Verified: {st.session_state.user_name}")
    st.sidebar.write(f"**Access Level:** {st.session_state.role.upper()}")
    
    if st.sidebar.button(t["logout_btn"], type="primary", use_container_width=True):
        for key in ['logged_in', 'role', 'user_name', 'user_id', 'customer_phone', 'customer_name', 'is_registered']:
            st.session_state[key] = None
        st.session_state.logged_in = False
        st.rerun()

st.title(f"🚑 {APP_NAME}")
st.write(t["sys_status"])
if not st.session_state.logged_in:
    st.warning(t["access_denied"])