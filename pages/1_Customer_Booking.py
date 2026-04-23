import streamlit as st
from shared_ui import render_top_bar
from database.queries import create_booking, register_customer, fetch_one
from utils.location_loader import get_divisions, get_districts, get_upazilas, is_valid_location_chain

st.set_page_config(page_title="Emergency Dispatch", layout="wide")
t = render_top_bar()  # 🎨 Injects the Dynamic Top Bar & CSS
st.title("🚑 Sina Rapid Response Terminal")

# --- FETCH SESSION DATA ---
c_phone = st.session_state.get('customer_phone', '')
c_name = st.session_state.get('customer_name', '')
is_reg = st.session_state.get('is_registered', 0)
is_logged_in = bool(c_phone)

tab1, tab2 = st.tabs(["🚨 Emergency Dispatch", "🔑 Member Registration"])

with tab1:
    # clear_on_submit is False because we don't want to wipe the auto-filled data
    with st.form("emergency_form", clear_on_submit=False):
        st.subheader("Patient Information")
        c1, c2 = st.columns(2)

        with c1:
            # If logged in, inject values and disable editing
            name = st.text_input("Patient Name *", value=c_name, disabled=is_logged_in)
            phone = st.text_input("Contact Phone *", value=c_phone, disabled=is_logged_in)

        with c2:
            urgency = st.select_slider("Urgency", options=["normal", "urgent", "critical"])

        st.subheader("Pickup Location")

        # --- Bangladesh structured location selection ---
        divisions = get_divisions()
        # FIX: column is name_en, not name
        division_names = [row["name_en"] for row in divisions]

        l1, l2, l3 = st.columns(3)

        with l1:
            selected_division = st.selectbox(
                "Division *",
                division_names,
                index=0 if division_names else None
            )

        # FIX: look up by name_en
        selected_division_id = next(
            (row["id"] for row in divisions if row["name_en"] == selected_division),
            None
        )

        districts = get_districts(selected_division_id) if selected_division_id else []
        # FIX: column is name_en, not name
        district_names = [row["name_en"] for row in districts]

        with l2:
            selected_district = st.selectbox(
                "District *",
                district_names,
                index=0 if district_names else None
            )

        # FIX: look up by name_en
        selected_district_id = next(
            (row["id"] for row in districts if row["name_en"] == selected_district),
            None
        )

        upazilas = get_upazilas(selected_district_id) if selected_district_id else []
        # FIX: column is name_en, not name
        upazila_names = [row["name_en"] for row in upazilas]

        with l3:
            selected_upazila = st.selectbox(
                "Upazila / Thana *",
                upazila_names,
                index=0 if upazila_names else None
            )

        pickup_detail = st.text_input(
            "Pickup Address / Landmark *",
            placeholder="House, road, hospital, market, nearby landmark..."
        )

        st.subheader("Medical Requirements")
        m1, m2, m3 = st.columns(3)
        with m1:
            ox = st.checkbox("Oxygen Support")
        with m2:
            icu = st.checkbox("ICU/Ventilator")
        with m3:
            nurse = st.checkbox("Nurse/Attendant")

        note = st.text_area(
            "Patient Condition / Medical Notes",
            placeholder="e.g. Cardiac arrest, respiratory distress..."
        )

        # --- SECURE MEMBER FEEDBACK ---
        if is_logged_in and is_reg == 1:
            st.success(f"✅ Logged in as {c_name}: 10% Discount will be applied automatically.")
        elif not is_logged_in:
            st.info("💡 Guest Mode: Standard rates apply. Register below for permanent discounts.")

        if st.form_submit_button("INITIATE IMMEDIATE DISPATCH", type="primary", use_container_width=True):
            # Enforce session data over manual input if logged in
            final_name = c_name if is_logged_in else name
            final_phone = c_phone if is_logged_in else phone

            if not final_name or not final_phone or not pickup_detail:
                st.error("Name, Phone, and Pickup Address are required for emergency dispatch.")
            elif not selected_division or not selected_district or not selected_upazila:
                st.error("Division, District, and Upazila are required.")
            elif not is_valid_location_chain(selected_division, selected_district, selected_upazila):
                st.error("Selected location is invalid. Please choose a valid Division, District, and Upazila.")
            else:
                structured_location = (
                    f"{pickup_detail}, {selected_upazila}, {selected_district}, {selected_division}, Bangladesh"
                )

                success, res = create_booking(
                    final_name,
                    final_phone,
                    structured_location,
                    urgency,
                    1 if ox else 0,
                    1 if icu else 0,
                    1 if nurse else 0,
                    note
                )

                if success:
                    st.balloons()
                    st.success(f"Emergency Unit Logged! Booking ID: {res['id']}")
                    if not is_logged_in:
                        # Clear form manually for guests
                        st.rerun()
                else:
                    st.warning(res)

with tab2:
    st.subheader("Sina Membership Program")
    if is_logged_in:
        st.success(f"You are currently logged in and registered as {c_name} ({c_phone}).")
    else:
        st.info("Create an account to receive a permanent 10% discount on all ambulance services.")
        with st.form("reg_form"):
            r_name = st.text_input("Full Name")
            r_phone = st.text_input("Phone Number")
            r_pass = st.text_input("Create Password", type="password")
            if st.form_submit_button("Verify & Activate Account"):
                if not r_name or not r_phone or not r_pass:
                    st.error("All fields are required.")
                else:
                    success, msg = register_customer(r_name, r_phone, r_pass)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
