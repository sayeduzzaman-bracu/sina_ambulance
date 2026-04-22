# pages/1_Customer_Booking.py
import streamlit as st
from shared_ui import render_top_bar
from database.queries import create_booking, register_customer, fetch_one

st.set_page_config(page_title="Emergency Dispatch", layout="wide")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS
st.title("🚑 Sina Rapid Response Terminal")

# --- FETCH SESSION DATA ---
c_phone = st.session_state.get('customer_phone', '')
c_name = st.session_state.get('customer_name', '')
is_reg = st.session_state.get('is_registered', 0)
is_logged_in = bool(c_phone)

tab1, tab2 = st.tabs(["🚨 Emergency Dispatch", "🔑 Member Registration"])

with tab1:
    # Clear_on_submit is False because we don't want to wipe the auto-filled data
    with st.form("emergency_form", clear_on_submit=False):
        st.subheader("Patient Information")
        c1, c2 = st.columns(2)
        with c1:
            # If logged in, inject values and disable editing
            name = st.text_input("Patient Name *", value=c_name, disabled=is_logged_in)
            phone = st.text_input("Contact Phone *", value=c_phone, disabled=is_logged_in)
        with c2:
            urgency = st.select_slider("Urgency", options=["normal", "urgent", "critical"])
            location = st.text_input("Pickup Address / Landmark *")

        st.subheader("Medical Requirements")
        m1, m2, m3 = st.columns(3)
        with m1: ox = st.checkbox("Oxygen Support")
        with m2: icu = st.checkbox("ICU/Ventilator")
        with m3: nurse = st.checkbox("Nurse/Attendant")
        
        note = st.text_area("Patient Condition / Medical Notes", placeholder="e.g. Cardiac arrest, respiratory distress...")

        # --- SECURE MEMBER FEEDBACK ---
        if is_logged_in and is_reg == 1:
            st.success(f"✅ Logged in as {c_name}: 10% Discount will be applied automatically.")
        elif not is_logged_in:
            st.info("💡 Guest Mode: Standard rates apply. Register below for permanent discounts.")

        if st.form_submit_button("INITIATE IMMEDIATE DISPATCH", type="primary", use_container_width=True):
            # Enforce session data over manual input if logged in
            final_name = c_name if is_logged_in else name
            final_phone = c_phone if is_logged_in else phone
            
            if not final_name or not final_phone or not location:
                st.error("Name, Phone, and Location are required for emergency dispatch.")
            else:
                success, res = create_booking(
                    final_name, final_phone, location, urgency, 
                    1 if ox else 0, 1 if icu else 0, 1 if nurse else 0, note
                )
                if success: 
                    st.balloons()
                    st.success(f"Emergency Unit Logged! Booking ID: {res['id']}")
                    if not is_logged_in:
                        # Clear form manually for guests
                        st.rerun()
                else: 
                    st.warning(res)

# Look for this section inside pages/1_Customer_Booking.py:

with tab2:
    st.subheader("Sina Membership Program")
    if is_logged_in:
        st.success(f"You are currently logged in and registered as {c_name} ({c_phone}).")
    else:
        st.info("Create an account to receive a permanent 10% discount on all ambulance services.")
        with st.form("reg_form"):
            r_name = st.text_input("Full Name")
            r_phone = st.text_input("Phone Number")
            r_pass = st.text_input("Create Password", type="password") # NEW
            if st.form_submit_button("Verify & Activate Account"):
                if not r_name or not r_phone or not r_pass:
                    st.error("All fields are required.")
                else:
                    success, msg = register_customer(r_name, r_phone, r_pass) # UPDATED
                    if success: st.success(msg)
                    else: st.warning(msg)