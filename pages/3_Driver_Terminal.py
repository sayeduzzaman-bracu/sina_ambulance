import streamlit as st
from shared_ui import render_top_bar
from database.queries import get_assigned_trip_for_driver, update_trip_status, get_driver_pending_collections, driver_confirm_cash_payment

st.set_page_config(page_title="Driver Terminal", layout="centered")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS

# --- SECURITY GATE ---
if st.session_state.get('role') != 'driver':
    st.error(t["drv_access_denied"])
    st.stop()

driver_id = st.session_state.user_id
st.title(t["drv_title"].format(st.session_state.user_name))

# --- PENDING CASH COLLECTIONS ---
collections = get_driver_pending_collections(driver_id)
if collections:
    st.error(t["drv_pending_cash"].format(len(collections)))
    for c in collections:
        with st.container(border=True):
            final = float(c['fare_amount']) * (1 - float(c['discount_applied'])/100)
            st.write(t["drv_patient"].format(c['customer_name']))
            st.subheader(t["drv_collect"].format(f"{final:,.2f}"))
            if st.button(t["drv_btn_confirm_cash"], key=f"cash_{c['trip_id']}", type="primary", use_container_width=True):
                driver_confirm_cash_payment(c['booking_id'], c['trip_id'])
                st.rerun()
st.divider()

# --- ACTIVE MISSION ---
mission = get_assigned_trip_for_driver(driver_id)

if not mission:
    st.success(t["drv_status_online"])
    if st.button(t["drv_btn_refresh"]): st.rerun()
else:
    status = mission['trip_status']
    with st.container(border=True):
        st.subheader(t["drv_mission"].format(mission['urgency'].upper()))
        st.write(t["drv_patient_loc"].format(mission['customer_name'], mission['pickup_location']))
        
        if status == 'assigned':
            c1, c2 = st.columns(2)
            if c1.button(t["drv_btn_accept"], use_container_width=True, type="primary"):
                update_trip_status(mission['trip_id'], 'accepted')
                st.rerun()
            if c2.button(t["drv_btn_reject"], use_container_width=True):
                update_trip_status(mission['trip_id'], 'rejected', driver_id)
                st.rerun()
        elif status == 'accepted':
            if st.button(t["drv_btn_enroute"], use_container_width=True, type="primary"):
                update_trip_status(mission['trip_id'], 'en_route')
                st.rerun()
        elif status == 'en_route':
            if st.button(t["drv_btn_arrived"], use_container_width=True, type="primary"):
                update_trip_status(mission['trip_id'], 'in_progress')
                st.rerun()
        elif status == 'in_progress':
            if st.button(t["drv_btn_completed"], use_container_width=True, type="primary"):
                update_trip_status(mission['trip_id'], 'completed', driver_id)
                st.rerun()