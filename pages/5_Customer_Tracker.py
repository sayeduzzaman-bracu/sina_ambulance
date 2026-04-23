# pages/5_Customer_Tracker.py
import streamlit as st
from shared_ui import render_top_bar
import folium
from streamlit_folium import st_folium
from database.queries import get_customer_active_status, accept_trip_fare, cancel_booking_by_customer

st.set_page_config(page_title="Track My Ambulance", layout="centered")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS
st.title(t["trk_title"])

c_phone = st.session_state.get('customer_phone', '')
is_logged_in = bool(c_phone)
phone_to_track = c_phone if is_logged_in else ""

if not is_logged_in:
    with st.form("track_form"):
        phone_input = st.text_input(t["trk_phone_input"])
        if st.form_submit_button(t["trk_btn_track"], type="primary"):
            phone_to_track = phone_input

if phone_to_track:
    data = get_customer_active_status(phone_to_track)
    
    if not data:
        st.info(t["trk_no_emergencies"])
        st.stop()

    # --- 🛑 FARE AGREEMENT GATE ---
    if data['trip_id'] and data['fare_amount'] > 0 and data['is_fare_accepted'] == 0:
        st.warning(t["trk_action_req"])
        with st.container(border=True):
            base_fare = float(data['fare_amount'])
            discount = float(data['discount_applied'])
            final = base_fare * (1 - discount/100)
            
            st.write(t["trk_base_fare"].format(f"{base_fare:,.2f}"))
            if discount > 0:
                st.write(t["trk_discount"].format(discount, f"{base_fare*(discount/100):,.2f}"))
            st.subheader(t["trk_total_payable"].format(f"{final:,.2f}"))
            
            st.info(t["trk_pay_info"])
            
            c1, c2 = st.columns(2)
            if c1.button(t["trk_btn_agree"], type="primary", use_container_width=True):
                accept_trip_fare(data['trip_id'])
                st.rerun()
            if c2.button(t["trk_btn_reject"], use_container_width=True):
                cancel_booking_by_customer(data['booking_id'])
                st.error(t["trk_cancelled"])
                st.rerun()
        st.stop() # Hides the map until they agree!

    # --- 🗺️ LIVE TRACKING (Only shows if Fare is accepted or not set yet) ---
    st.success(t["trk_tracking_msg"].format(phone_to_track))
    
    stages = ["pending", "assigned", "accepted", "en_route", "in_progress", "completed"]
    curr = data['trip_status'] if data['trip_status'] else data['booking_status']
    
    # Translate status text for progress bar
    status_display = t.get(f"status_{curr}", curr.upper().replace('_', ' '))
    st.progress((stages.index(curr) + 1) / len(stages), text=f"{t['trk_status_lbl']}: {status_display}")
    
    if data['booking_status'] == 'pending':
        st.warning(t["trk_searching"])
    else:
        with st.container(border=True):
            if data['trip_source'] == 'sina':
                st.success(t["trk_sina_assigned"])
                st.write(t["trk_driver_details"].format(data['driver_name'], data['driver_phone']))
            else:
                st.success(t["trk_partner_assigned"])
                st.write(t["trk_partner_details"].format(data['supplier_name'], data['supplier_phone']))

        if data['trip_source'] == 'sina' and data['last_lat'] != 0.0:
            m = folium.Map(location=[data['last_lat'], data['last_lng']], zoom_start=14)
            folium.Marker([data['last_lat'], data['last_lng']], popup=t["trk_popup_amb"], icon=folium.Icon(color="blue", icon="ambulance", prefix="fa")).add_to(m)
            if data['pickup_lat'] != 0.0:
                folium.Marker([data['pickup_lat'], data['pickup_lng']], popup=t["trk_popup_you"], icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)
            st_folium(m, height=350, use_container_width=True)
            if st.button(t["trk_btn_refresh"]): st.rerun()