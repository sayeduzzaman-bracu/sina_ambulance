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
    st.warning("Please log in via the Sidebar to view your bills and download receipts.")
    st.stop()

st.title("💳 Billing & Receipts")
st.success(f"Secure portal open for: {c_name} ({c_phone})")

# Create tabs for Unpaid vs Paid trips
tab1, tab2 = st.tabs(["⚠️ Pending Invoices", "🧾 Payment History & Receipts"])

with tab1:
    unpaid_bills = get_unpaid_bills_for_customer(c_phone)
    if not unpaid_bills:
        st.info("🎉 You have no outstanding bills! All completed trips are fully paid.")
    else:
        st.subheader("Outstanding Invoices")
        for bill in unpaid_bills:
            with st.container(border=True):
                st.write(f"**Trip #{bill['trip_id']}** | Completed: {bill['completed_at']}")
                st.caption(f"Route: {bill['pickup_location']} ➔ Medical Facility/Hospital")
                
                base_fare = float(bill['fare_amount'] or 0)
                discount_percent = float(bill['discount_applied'] or 0)
                
                if base_fare == 0:
                    st.warning("⏳ Calculating fare... Please wait for the Manager to finalize the bill.")
                    continue
                
                discount_amount = base_fare * (discount_percent / 100)
                final_payable = base_fare - discount_amount
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Base Fare: `৳{base_fare:,.2f}`")
                    if discount_percent > 0:
                        st.write(f"Member Discount ({discount_percent}%): `:green[- ৳{discount_amount:,.2f}]`")
                    st.subheader(f"Total Due: ৳{final_payable:,.2f}")
                    
                with col2:
                    payment_method = st.selectbox("Select Payment Method", ["bKash (Mobile Money)", "SSLCommerz (Card)", "Cash to Driver"], key=f"pay_method_{bill['booking_id']}")
                    if st.button("🔒 Pay Securely Now", key=f"pay_btn_{bill['booking_id']}", type="primary"):
                        if payment_method == "Cash to Driver":
                            st.info("Please hand the exact amount to the driver. They will clear this invoice.")
                        else:
                            with st.spinner("Processing Payment..."):
                                success, msg = process_customer_payment(bill['booking_id'], payment_method)
                                if success:
                                    st.success("✅ Payment Authorized!")
                                    st.rerun()

with tab2:
    paid_bills = get_paid_bills_for_customer(c_phone)
    if not paid_bills:
        st.info("No payment history found.")
    else:
        st.subheader("Completed Transactions")
        for bill in paid_bills:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Trip #{bill['trip_id']}** | Paid on: {bill['completed_at']}")
                    st.write(f"Status: ✅ **PAID**")
                with c2:
                    # Generate the PDF file path in the background
                    pdf_path = generate_pdf_receipt(bill, c_name, c_phone)
                    
                    # Read the PDF file to create a download button
                    with open(pdf_path, "rb") as pdf_file:
                        PDFbyte = pdf_file.read()
                        
                    st.download_button(
                        label="📄 Download Receipt",
                        data=PDFbyte,
                        file_name=f"Sina_Receipt_Trip_{bill['trip_id']}.pdf",
                        mime='application/octet-stream',
                        key=f"dl_{bill['trip_id']}"
                    )