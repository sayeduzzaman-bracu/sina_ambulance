# pages/6_Customer_Billing.py
import streamlit as st
from shared_ui import render_top_bar
import os
from database.queries import get_unpaid_bills_for_customer, get_paid_bills_for_customer, process_customer_payment
from receipt_generator import generate_pdf_receipt

st.set_page_config(page_title="Secure Checkout", layout="centered")
t = render_top_bar() # 🎨 Injects the Dynamic Top Bar & CSS

c_phone = st.session_state.get('customer_phone', '')
c_name = st.session_state.get('customer_name', '')
is_logged_in = bool(c_phone)

if not is_logged_in:
    st.warning(t["bil_login_warning"])
    st.stop()

st.title(t["bil_title"])
st.success(t["bil_portal_open"].format(c_name, c_phone))

# Create tabs for Unpaid vs Paid trips
tab1, tab2 = st.tabs([t["bil_tab_pending"], t["bil_tab_history"]])

with tab1:
    unpaid_bills = get_unpaid_bills_for_customer(c_phone)
    if not unpaid_bills:
        st.info(t["bil_no_unpaid"])
    else:
        st.subheader(t["bil_outstanding"])
        for bill in unpaid_bills:
            with st.container(border=True):
                st.write(t["bil_trip_completed"].format(bill['trip_id'], bill['completed_at']))
                st.caption(t["bil_route"].format(bill['pickup_location']))
                
                base_fare = float(bill['fare_amount'] or 0)
                discount_percent = float(bill['discount_applied'] or 0)
                
                if base_fare == 0:
                    st.warning(t["bil_calc_fare"])
                    continue
                
                discount_amount = base_fare * (discount_percent / 100)
                final_payable = base_fare - discount_amount
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(t["bil_base_fare"].format(f"{base_fare:,.2f}"))
                    if discount_percent > 0:
                        st.write(t["bil_discount"].format(discount_percent, f"{discount_amount:,.2f}"))
                    st.subheader(t["bil_total_due"].format(f"{final_payable:,.2f}"))
                    
                with col2:
                    pay_opts = ["bKash (Mobile Money)", "SSLCommerz (Card)", "Cash to Driver"]
                    payment_method = st.selectbox(
                        t["bil_select_pay"], 
                        pay_opts, 
                        key=f"pay_method_{bill['booking_id']}",
                        format_func=lambda x: t.get(x, x)
                    )
                    
                    if st.button(t["bil_btn_pay_now"], key=f"pay_btn_{bill['booking_id']}", type="primary"):
                        if payment_method == "Cash to Driver":
                            st.info(t["bil_cash_info"])
                        else:
                            with st.spinner(t["bil_processing"]):
                                success, msg = process_customer_payment(bill['booking_id'], payment_method)
                                if success:
                                    st.success(t["bil_pay_success"])
                                    st.rerun()

with tab2:
    paid_bills = get_paid_bills_for_customer(c_phone)
    if not paid_bills:
        st.info(t["bil_no_history"])
    else:
        st.subheader(t["bil_completed_trans"])
        for bill in paid_bills:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(t["bil_paid_on"].format(bill['trip_id'], bill['completed_at']))
                    st.write(t["bil_status_paid"])
                with c2:
                    # Generate the PDF file path in the background
                    pdf_path = generate_pdf_receipt(bill, c_name, c_phone)
                    
                    # Read the PDF file to create a download button
                    with open(pdf_path, "rb") as pdf_file:
                        PDFbyte = pdf_file.read()
                        
                    st.download_button(
                        label=t["bil_btn_download"],
                        data=PDFbyte,
                        file_name=f"Sina_Receipt_Trip_{bill['trip_id']}.pdf",
                        mime='application/octet-stream',
                        key=f"dl_{bill['trip_id']}"
                    )