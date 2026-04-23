# pages/4_Finance_Center.py
import streamlit as st
from shared_ui import render_top_bar
from database.queries import get_completed_missions, finalize_finance

st.set_page_config(page_title="Finance Center", layout="wide")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS

# --- SECURITY GATE ---
if st.session_state.get('role') != 'manager':
    st.error("🛑 ACCESS DENIED: Only System Administrators can view the Finance Center.")
    st.stop()

st.title("💰 Finance & Risk Management")
st.write("Review completed trips, verify discounts, and finalize base fares.")

missions = get_completed_missions()
if not missions:
    st.info("No completed trips to process.")
else:
    for m in missions:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Trip #{m['id']}** ({m['trip_source'].upper()})")
                st.caption(f"Patient: {m['customer_name']}")
                st.write(f"**Current Status:** `{m['payment_status'].upper()}`")
            with col2:
                fare = st.number_input("Base Fare (৳)", value=float(m['fare_amount'] or 0), key=f"f_{m['id']}")
                disc = m['discount_applied']
                final = fare * (1 - disc/100)
                st.write(f"**Applied Discount:** {disc}%")
                st.write(f"**Final Due from Patient:** :green[৳{final:,.2f}]")
            with col3:
                # Allow manager to manually override payment status if needed
                p_opts = ["pending", "paid", "disputed"]
                current_idx = p_opts.index(m['payment_status']) if m['payment_status'] in p_opts else 0
                
                p_status = st.selectbox("Payment Status", p_opts, index=current_idx, key=f"ps_{m['id']}")
                if st.button("Verify & Save Bill", key=f"sv_{m['id']}", type="primary"):
                    finalize_finance(m['id'], fare, m['b_id'], p_status)
                    st.success("Finance record updated successfully.")
                    st.rerun()