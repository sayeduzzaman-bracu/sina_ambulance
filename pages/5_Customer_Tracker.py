# pages/5_Customer_Tracker.py
import streamlit as st
from shared_ui import render_top_bar
import folium
from streamlit_folium import st_folium
from database.queries import get_customer_active_status, accept_trip_fare, cancel_booking_by_customer

st.set_page_config(page_title="Track My Ambulance", layout="centered")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS
st.title("📍 Sina Live Tracker")

c_phone = st.session_state.get('customer_phone', '')
is_logged_in = bool(c_phone)
phone_to_track = c_phone if is_logged_in else ""

if not is_logged_in:
    with st.form("track_form"):
        phone_input = st.text_input("Enter your phone number to track")
        if st.form_submit_button("Track", type="primary"):
            phone_to_track = phone_input

if phone_to_track:
    data = get_customer_active_status(phone_to_track)
    
    if not data:
        st.info("No active emergencies found.")
        st.stop()

    # --- 🛑 FARE AGREEMENT GATE ---
    if data['trip_id'] and data['fare_amount'] > 0 and data['is_fare_accepted'] == 0:
        st.warning("⚠️ Action Required: Please review the dispatch fare.")
        with st.container(border=True):
            base_fare = float(data['fare_amount'])
            discount = float(data['discount_applied'])
            final = base_fare * (1 - discount/100)
            
            st.write(f"**Proposed Base Fare:** ৳{base_fare:,.2f}")
            if discount > 0:
                st.write(f"**Member Discount ({discount}%):** :green[- ৳{base_fare*(discount/100):,.2f}]")
            st.subheader(f"Total Payable: ৳{final:,.2f}")
            
            st.info("You can pay securely in the app later, or pay cash to the driver upon completion.")
            
            c1, c2 = st.columns(2)
            if c1.button("✅ I Agree, Dispatch Unit", type="primary", use_container_width=True):
                accept_trip_fare(data['trip_id'])
                st.rerun()
            if c2.button("❌ Reject & Cancel Trip", use_container_width=True):
                cancel_booking_by_customer(data['booking_id'])
                st.error("Trip Cancelled.")
                st.rerun()
        st.stop() # Hides the map until they agree!

    # --- 🗺️ LIVE TRACKING (Only shows if Fare is accepted or not set yet) ---
    st.success(f"Tracking active emergency for {phone_to_track}")
    
    stages = ["pending", "assigned", "accepted", "en_route", "in_progress", "completed"]
    curr = data['trip_status'] if data['trip_status'] else data['booking_status']
    st.progress((stages.index(curr) + 1) / len(stages), text=f"Status: {curr.upper().replace('_', ' ')}")
    
    if data['booking_status'] == 'pending':
        st.warning("🔄 Searching for the nearest available unit...")
    else:
        with st.container(border=True):
            if data['trip_source'] == 'sina':
                st.success("✅ Sina Unit Assigned")
                st.write(f"**Driver:** {data['driver_name']} | 📞 {data['driver_phone']}")
            else:
                st.success("✅ Partner Unit Assigned")
                st.write(f"**Company:** {data['supplier_name']} | 📞 {data['supplier_phone']}")

        if data['trip_source'] == 'sina' and data['last_lat'] != 0.0:
            m = folium.Map(location=[data['last_lat'], data['last_lng']], zoom_start=14)
            folium.Marker([data['last_lat'], data['last_lng']], popup="Ambulance", icon=folium.Icon(color="blue", icon="ambulance", prefix="fa")).add_to(m)
            if data['pickup_lat'] != 0.0:
                folium.Marker([data['pickup_lat'], data['pickup_lng']], popup="You", icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)
            st_folium(m, height=350, use_container_width=True)
            if st.button("🔄 Refresh Location"): st.rerun()