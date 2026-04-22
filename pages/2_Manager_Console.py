# pages/2_Manager_Console.py
import streamlit as st
from shared_ui import render_top_bar
import folium
from streamlit_folium import st_folium
from database.queries import (
    get_pending_bookings, get_available_sina_drivers, get_all_suppliers, 
    dispatch_mission, get_live_map_data, register_driver, register_admin
)

st.set_page_config(page_title="Sina Command Center", layout="wide")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS

# --- SECURITY GATE ---
if st.session_state.get('role') != 'manager':
    st.error("🛑 ACCESS DENIED: Only System Administrators can view this console.")
    st.stop()

st.title(f"🗺️ Command Center: {st.session_state.get('user_name', 'Admin')}")

# Insert this right ABOVE the tab1, tab2, tab3 = st.tabs(...) line in 2_Manager_Console.py

st.markdown("### 📊 Live System Diagnostics")
# Fetch counts for the metrics
total_drivers = len(get_available_sina_drivers())
pending_emergencies = len(get_pending_bookings())
# Create beautiful metric cards
m1, m2, m3, m4 = st.columns(4)
m1.metric("System Status", "ONLINE", "Secure")
m2.metric("Active Emergencies", f"{pending_emergencies}", "- Priority" if pending_emergencies > 0 else "Clear")
m3.metric("Available Sina Units", f"{total_drivers}", "Ready to Dispatch")
m4.metric("Partner Network", "Active", "SLA 99.9%")
st.divider()

# Added a 3rd Tab for HR & Staff Management
tab1, tab2, tab3 = st.tabs(["📡 Live Fleet Radar", "📋 Dispatch Queue", "👔 Staff Management"])

with tab1:
    st.subheader("Global Fleet & Emergency Positioning")
    st.info("Map centers on Dhaka, Bangladesh. GPS coordinates are updated live by Driver Terminals.")
    
    m = folium.Map(location=[23.8103, 90.4125], zoom_start=12, tiles="cartodbpositron")
    drivers, pending, active = get_live_map_data()
    
    for d in drivers:
        color = "blue" if d['is_available'] == 1 else "gray"
        folium.Marker([d['last_lat'], d['last_lng']], popup=f"Unit: {d['full_name']}", icon=folium.Icon(color=color, icon="ambulance", prefix="fa")).add_to(m)
        
    for p in pending:
        folium.Marker([p['pickup_lat'], p['pickup_lng']], popup=f"EMERGENCY: {p['customer_name']}", icon=folium.Icon(color="red", icon="warning", prefix="fa")).add_to(m)

    st_folium(m, width=1200, height=500)

with tab2:
    st.subheader("Action Required: Pending Emergencies")
    pending_reqs = get_pending_bookings()
    
    if not pending_reqs:
        st.success("No pending emergencies.")
    else:
        for req in pending_reqs:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.write(f"**#{req['id']}** | Patient: {req['customer_name']} ({req['urgency'].upper()})")
                    st.caption(f"📍 {req['pickup_location']}")
                    
                    med_reqs = []
                    if req.get('oxygen_needed') == 1: med_reqs.append("Oxygen")
                    if req.get('icu_needed') == 1: med_reqs.append("ICU")
                    if req.get('nurse_needed') == 1: med_reqs.append("Nurse")
                    if med_reqs: st.write(f"**Required:** {', '.join(med_reqs)}")
                
                with c2:
                    d_opts = {f"Sina: {d['full_name']}": d['id'] for d in get_available_sina_drivers()}
                    sel_d = st.selectbox("Assign Sina Unit", options=list(d_opts.keys()), index=None, key=f"d_{req['id']}")
                    if st.button("Dispatch Sina Priority", key=f"bd_{req['id']}", type="primary"):
                        if sel_d: 
                            dispatch_mission(req['id'], 'sina', driver_id=d_opts[sel_d])
                            st.rerun()
                
                with c3:
                    s_opts = {f"Partner: {s['company_name']}": s['id'] for s in get_all_suppliers()}
                    sel_s = st.selectbox("Partner Backup", options=list(s_opts.keys()), index=None, key=f"s_{req['id']}")
                    if st.button("Handoff to Partner", key=f"bs_{req['id']}"):
                        if sel_s:
                            dispatch_mission(req['id'], 'external', supplier_id=s_opts[sel_s])
                            st.rerun()

with tab3:
    st.subheader("Human Resources & Fleet Expansion")
    st.write("Secure portal to onboard vetted drivers and assign system managers.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("add_driver_form", clear_on_submit=True):
            st.write("🚑 **Register New Driver**")
            d_name = st.text_input("Driver Full Name")
            d_phone = st.text_input("Driver Phone Number")
            d_pass = st.text_input("Assign Temporary Password", type="password")
            
            if st.form_submit_button("Create Driver Profile", type="primary", use_container_width=True):
                if not d_name or not d_phone or not d_pass:
                    st.error("All fields are required.")
                else:
                    success, msg = register_driver(d_name, d_phone, d_pass)
                    if success: st.success(msg)
                    else: st.warning(msg)
                    
    with col2:
        with st.form("add_admin_form", clear_on_submit=True):
            st.write("👔 **Register New Manager**")
            a_name = st.text_input("Manager Username")
            a_pass = st.text_input("Create Password", type="password")
            
            if st.form_submit_button("Create Manager Account", type="primary", use_container_width=True):
                if not a_name or not a_pass:
                    st.error("Username and Password are required.")
                else:
                    success, msg = register_admin(a_name, a_pass)
                    if success: st.success(msg)
                    else: st.warning(msg)