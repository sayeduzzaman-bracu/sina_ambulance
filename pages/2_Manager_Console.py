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
    st.error(t["mgr_access_denied"])
    st.stop()

# Fallback in case user_name is missing, translate "Admin" as well
admin_name = st.session_state.get('user_name', t["mgr_admin_fallback"])
st.title(t["mgr_title"].format(admin_name))

st.markdown(t["mgr_diagnostics"])
# Fetch counts for the metrics
total_drivers = len(get_available_sina_drivers())
pending_emergencies = len(get_pending_bookings())

# Create beautiful metric cards
m1, m2, m3, m4 = st.columns(4)
m1.metric(t["mgr_sys_status"], t["mgr_online"], t["mgr_secure"])
m2.metric(t["mgr_active_emerg"], f"{pending_emergencies}", t["mgr_priority"] if pending_emergencies > 0 else t["mgr_clear"])
m3.metric(t["mgr_avail_units"], f"{total_drivers}", t["mgr_ready_dispatch"])
m4.metric(t["mgr_partner_net"], t["mgr_active"], t["mgr_sla"])
st.divider()

# Added a 3rd Tab for HR & Staff Management
tab1, tab2, tab3 = st.tabs([t["mgr_tab_radar"], t["mgr_tab_queue"], t["mgr_tab_hr"]])

with tab1:
    st.subheader(t["mgr_radar_sub"])
    st.info(t["mgr_radar_info"])
    
    m = folium.Map(location=[23.8103, 90.4125], zoom_start=12, tiles="cartodbpositron")
    drivers, pending, active = get_live_map_data()
    
    for d in drivers:
        color = "blue" if d['is_available'] == 1 else "gray"
        folium.Marker(
            [d['last_lat'], d['last_lng']], 
            popup=f"{t['mgr_unit']}: {d['full_name']}", 
            icon=folium.Icon(color=color, icon="ambulance", prefix="fa")
        ).add_to(m)
        
    for p in pending:
        folium.Marker(
            [p['pickup_lat'], p['pickup_lng']], 
            popup=f"{t['mgr_emergency']}: {p['customer_name']}", 
            icon=folium.Icon(color="red", icon="warning", prefix="fa")
        ).add_to(m)

    st_folium(m, width=1200, height=500)

with tab2:
    st.subheader(t["mgr_queue_sub"])
    pending_reqs = get_pending_bookings()
    
    if not pending_reqs:
        st.success(t["mgr_no_pending"])
    else:
        for req in pending_reqs:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.write(f"**#{req['id']}** | {t['mgr_patient']}: {req['customer_name']} ({req['urgency'].upper()})")
                    st.caption(f"📍 {req['pickup_location']}")
                    
                    med_reqs = []
                    if req.get('oxygen_needed') == 1: med_reqs.append(t["mgr_oxy"])
                    if req.get('icu_needed') == 1: med_reqs.append(t["mgr_icu"])
                    if req.get('nurse_needed') == 1: med_reqs.append(t["mgr_nurse"])
                    if med_reqs: st.write(f"**{t['mgr_required']}:** {', '.join(med_reqs)}")
                
                with c2:
                    d_opts = {f"{t['mgr_sina']}: {d['full_name']}": d['id'] for d in get_available_sina_drivers()}
                    sel_d = st.selectbox(t["mgr_assign_sina"], options=list(d_opts.keys()), index=None, key=f"d_{req['id']}")
                    if st.button(t["mgr_btn_dispatch_sina"], key=f"bd_{req['id']}", type="primary"):
                        if sel_d: 
                            dispatch_mission(req['id'], 'sina', driver_id=d_opts[sel_d])
                            st.rerun()
                
                with c3:
                    s_opts = {f"{t['mgr_partner']}: {s['company_name']}": s['id'] for s in get_all_suppliers()}
                    sel_s = st.selectbox(t["mgr_partner_backup"], options=list(s_opts.keys()), index=None, key=f"s_{req['id']}")
                    if st.button(t["mgr_btn_handoff"], key=f"bs_{req['id']}"):
                        if sel_s:
                            dispatch_mission(req['id'], 'external', supplier_id=s_opts[sel_s])
                            st.rerun()

with tab3:
    st.subheader(t["mgr_hr_sub"])
    st.write(t["mgr_hr_info"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("add_driver_form", clear_on_submit=True):
            st.write(t["mgr_reg_driver"])
            d_name = st.text_input(t["mgr_d_name"])
            d_phone = st.text_input(t["mgr_d_phone"])
            d_pass = st.text_input(t["mgr_d_pass"], type="password")
            
            if st.form_submit_button(t["mgr_btn_create_d"], type="primary", use_container_width=True):
                if not d_name or not d_phone or not d_pass:
                    st.error(t["mgr_err_all_req"])
                else:
                    success, msg = register_driver(d_name, d_phone, d_pass)
                    if success: st.success(msg)
                    else: st.warning(msg)
                    
    with col2:
        with st.form("add_admin_form", clear_on_submit=True):
            st.write(t["mgr_reg_mgr"])
            a_name = st.text_input(t["mgr_m_name"])
            a_pass = st.text_input(t["mgr_m_pass"], type="password")
            
            if st.form_submit_button(t["mgr_btn_create_m"], type="primary", use_container_width=True):
                if not a_name or not a_pass:
                    st.error(t["mgr_err_m_req"])
                else:
                    success, msg = register_admin(a_name, a_pass)
                    if success: st.success(msg)
                    else: st.warning(msg)