import streamlit as st
from shared_ui import render_top_bar
from database.queries import get_completed_missions, finalize_finance

st.set_page_config(page_title="Finance Center", layout="wide")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS

# --- SECURITY GATE ---
if st.session_state.get('role') != 'manager':
    st.error(t["fin_access_denied"])
    st.stop()

st.title(t["fin_title"])
st.write(t["fin_subtitle"])

missions = get_completed_missions()
if not missions:
    st.info(t["fin_no_trips"])
else:
    for m in missions:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(t["fin_trip"].format(m['id'], m['trip_source'].upper()))
                st.caption(t["fin_patient"].format(m['customer_name']))
                # Display current status using the dictionary if mapped, otherwise default to the string
                st.write(t["fin_curr_status"].format(m['payment_status'].upper()))
            with col2:
                fare = st.number_input(t["fin_base_fare"], value=float(m['fare_amount'] or 0), key=f"f_{m['id']}")
                disc = m['discount_applied']
                final = fare * (1 - disc/100)
                st.write(t["fin_discount"].format(disc))
                st.write(t["fin_final_due"].format(final))
            with col3:
                # Allow manager to manually override payment status if needed
                p_opts = ["pending", "paid", "disputed"]
                current_idx = p_opts.index(m['payment_status']) if m['payment_status'] in p_opts else 0
                
                # Use format_func to translate the UI while keeping the database values intact
                p_status = st.selectbox(
                    t["fin_pay_status_lbl"], 
                    p_opts, 
                    index=current_idx, 
                    key=f"ps_{m['id']}",
                    format_func=lambda x: t.get(f"fin_status_{x}", x.title())
                )
                if st.button(t["fin_btn_verify"], key=f"sv_{m['id']}", type="primary"):
                    finalize_finance(m['id'], fare, m['b_id'], p_status)
                    st.success(t["fin_success_msg"])
                    st.rerun()