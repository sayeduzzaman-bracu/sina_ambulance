import streamlit as st
from shared_ui import render_top_bar
from database.queries import create_booking, register_customer, fetch_one
from utils.location_loader import get_divisions, get_districts, get_upazilas, is_valid_location_chain

st.set_page_config(page_title="Emergency Dispatch", layout="wide")
t = render_top_bar()  # 🎨 Injects the Dynamic Top Bar & CSS
st.title(t["page_header"])

# --- FETCH SESSION DATA ---
c_phone = st.session_state.get('customer_phone', '')
c_name = st.session_state.get('customer_name', '')
is_reg = st.session_state.get('is_registered', 0)
is_logged_in = bool(c_phone)

tab1, tab2 = st.tabs([t["tab_dispatch"], t["tab_reg"]])

with tab1:
    # clear_on_submit is False because we don't want to wipe the auto-filled data
    with st.form("emergency_form", clear_on_submit=False):
        st.subheader(t["patient_info_header"])
        c1, c2 = st.columns(2)

        with c1:
            # If logged in, inject values and disable editing
            name = st.text_input(t["patient_name_lbl"], value=c_name, disabled=is_logged_in)
            phone = st.text_input(t["contact_phone_lbl"], value=c_phone, disabled=is_logged_in)

        with c2:
            # format_func translates the display text while keeping the db values (normal/urgent/critical) intact
            urgency = st.select_slider(
                t["urgency_lbl"], 
                options=["normal", "urgent", "critical"],
                format_func=lambda x: t.get(f"urgency_{x}", x)
            )

        st.subheader(t["pickup_loc_header"])

        # --- Bangladesh structured location selection ---
        divisions = get_divisions()
        division_names = [row["name_en"] for row in divisions]

        l1, l2, l3 = st.columns(3)

        with l1:
            selected_division = st.selectbox(
                t["division_lbl"],
                division_names,
                index=0 if division_names else None
            )

        selected_division_id = next(
            (row["id"] for row in divisions if row["name_en"] == selected_division),
            None
        )

        districts = get_districts(selected_division_id) if selected_division_id else []
        district_names = [row["name_en"] for row in districts]

        with l2:
            selected_district = st.selectbox(
                t["district_lbl"],
                district_names,
                index=0 if district_names else None
            )

        selected_district_id = next(
            (row["id"] for row in districts if row["name_en"] == selected_district),
            None
        )

        upazilas = get_upazilas(selected_district_id) if selected_district_id else []
        upazila_names = [row["name_en"] for row in upazilas]

        with l3:
            selected_upazila = st.selectbox(
                t["upazila_lbl"],
                upazila_names,
                index=0 if upazila_names else None
            )

        pickup_detail = st.text_input(
            t["pickup_addr_lbl"],
            placeholder=t["pickup_addr_ph"]
        )

        st.subheader(t["med_req_header"])
        m1, m2, m3 = st.columns(3)
        with m1:
            ox = st.checkbox(t["ox_lbl"])
        with m2:
            icu = st.checkbox(t["icu_lbl"])
        with m3:
            nurse = st.checkbox(t["nurse_lbl"])

        note = st.text_area(
            t["med_notes_lbl"],
            placeholder=t["med_notes_ph"]
        )

        # --- SECURE MEMBER FEEDBACK ---
        if is_logged_in and is_reg == 1:
            st.success(t["logged_in_discount"].format(c_name))
        elif not is_logged_in:
            st.info(t["guest_mode_msg"])

        if st.form_submit_button(t["dispatch_btn"], type="primary", use_container_width=True):
            # Enforce session data over manual input if logged in
            final_name = c_name if is_logged_in else name
            final_phone = c_phone if is_logged_in else phone

            if not final_name or not final_phone or not pickup_detail:
                st.error(t["err_req_fields"])
            elif not selected_division or not selected_district or not selected_upazila:
                st.error(t["err_loc_fields"])
            elif not is_valid_location_chain(selected_division, selected_district, selected_upazila):
                st.error(t["err_invalid_loc"])
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
                    st.success(f"{t['success_dispatch']} {res['id']}")
                    if not is_logged_in:
                        st.rerun()
                else:
                    st.warning(res)

with tab2:
    st.subheader(t["membership_header"])
    if is_logged_in:
        st.success(t["logged_in_reg"].format(c_name, c_phone))
    else:
        st.info(t["create_acc_msg"])
        with st.form("reg_form"):
            r_name = st.text_input(t["reg_name_lbl"])
            r_phone = st.text_input(t["reg_phone_lbl"])
            r_pass = st.text_input(t["reg_pass_lbl"], type="password")
            if st.form_submit_button(t["reg_btn"]):
                if not r_name or not r_phone or not r_pass:
                    st.error(t["err_all_req"])
                else:
                    success, msg = register_customer(r_name, r_phone, r_pass)
                    if success:
                        st.success(msg)
                    else:
                        st.warning(msg)
