# pages/3_Driver_Terminal.py
import streamlit as st
from shared_ui import render_top_bar
from database.queries import get_assigned_trip_for_driver, update_trip_status, get_driver_pending_collections, driver_confirm_cash_payment

st.set_page_config(page_title="Driver Terminal", layout="centered")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS

# --- SECURITY GATE ---
if st.session_state.get('role') != 'driver':
    st.error("🛑 ACCESS DENIED: Only verified drivers can view this terminal.")
    st.stop()

driver_id = st.session_state.user_id
st.title(f"📲 Terminal: {st.session_state.user_name}")

# --- PENDING CASH COLLECTIONS ---
collections = get_driver_pending_collections(driver_id)
if collections:
    st.error(f"⚠️ You have {len(collections)} pending cash collections!")
    for c in collections:
        with st.container(border=True):
            final = float(c['fare_amount']) * (1 - float(c['discount_applied'])/100)
            st.write(f"**Patient:** {c['customer_name']}")
            st.subheader(f"Collect: ৳{final:,.2f}")
            if st.button("✅ Confirm Cash Received", key=f"cash_{c['trip_id']}", type="primary", use_container_width=True):
                driver_confirm_cash_payment(c['booking_id'], c['trip_id'])
                st.rerun()
st.divider()

# --- ACTIVE MISSION ---
mission = get_assigned_trip_for_driver(driver_id)

if not mission:
    st.success("STATUS: ONLINE | Waiting for dispatch...")
    if st.button("🔄 Refresh System"): st.rerun()
else:
    status = mission['trip_status']
    with st.container(border=True):
        st.subheader(f"Mission: {mission['urgency'].upper()}")
        st.write(f"Patient: {mission['customer_name']} | 📍 {mission['pickup_location']}")
        
        if status == 'assigned':
            c1, c2 = st.columns(2)
            if c1.button("✅ ACCEPT", use_container_width=True, type="primary"):
                update_trip_status(mission['trip_id'], 'accepted')
                st.rerun()
            if c2.button("❌ REJECT", use_container_width=True):
                update_trip_status(mission['trip_id'], 'rejected', driver_id)
                st.rerun()
        elif status == 'accepted':
            if st.button("🚀 EN-ROUTE", use_container_width=True, type="primary"):
                update_trip_status(mission['trip_id'], 'en_route')
                st.rerun()
        elif status == 'en_route':
            if st.button("📍 ARRIVED", use_container_width=True, type="primary"):
                update_trip_status(mission['trip_id'], 'in_progress')
                st.rerun()
        elif status == 'in_progress':
            if st.button("🏁 COMPLETED", use_container_width=True, type="primary"):
                update_trip_status(mission['trip_id'], 'completed', driver_id)
                st.rerun()