# receipt_generator.py
from fpdf import FPDF
import tempfile
import os

def generate_pdf_receipt(trip_data, customer_name, customer_phone):
    """Generates a professional PDF invoice and returns the file path."""
    pdf = FPDF()
    pdf.add_page()
    
    # --- Header ---
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(0, 10, txt="SINA AMBULANCE DISPATCH", ln=True, align='C')
    
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, txt="Official Medical Transport Invoice", ln=True, align='C')
    pdf.ln(10)
    
    # --- Patient & Trip Details ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="BILLING DETAILS", ln=True)
    pdf.set_font("Arial", '', 12)
    
    pdf.cell(40, 8, txt="Patient Name:", ln=False)
    pdf.cell(0, 8, txt=f"{customer_name}", ln=True)
    
    pdf.cell(40, 8, txt="Phone Number:", ln=False)
    pdf.cell(0, 8, txt=f"{customer_phone}", ln=True)
    
    pdf.cell(40, 8, txt="Trip ID:", ln=False)
    pdf.cell(0, 8, txt=f"#{trip_data['trip_id']} (Booking #{trip_data['booking_id']})", ln=True)
    
    pdf.cell(40, 8, txt="Date Completed:", ln=False)
    pdf.cell(0, 8, txt=f"{trip_data['completed_at']}", ln=True)
    
    pdf.cell(40, 8, txt="Route:", ln=False)
    pdf.cell(0, 8, txt=f"{trip_data['pickup_location']} -> Medical Facility", ln=True)
    
    pdf.ln(10)
    
    # --- Financial Breakdown ---
    base_fare = float(trip_data['fare_amount'] or 0)
    discount_percent = float(trip_data['discount_applied'] or 0)
    discount_amount = base_fare * (discount_percent / 100)
    final_payable = base_fare - discount_amount
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="FINANCIAL BREAKDOWN", ln=True)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(140, 10, txt="Base Transport Fare:", ln=False)
    pdf.cell(50, 10, txt=f"BDT {base_fare:,.2f}", ln=True, align='R')
    
    if discount_percent > 0:
        pdf.cell(140, 10, txt=f"Membership Discount ({discount_percent}%):", ln=False)
        pdf.cell(50, 10, txt=f"- BDT {discount_amount:,.2f}", ln=True, align='R')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(140, 15, txt="TOTAL PAID:", ln=False)
    pdf.cell(50, 15, txt=f"BDT {final_payable:,.2f}", ln=True, align='R')
    
    # --- Footer ---
    pdf.ln(30)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt="Thank you for trusting Sina Ambulance Service in your time of need.", ln=True, align='C')
    pdf.cell(0, 5, txt="For support, please contact dispatch at 16000.", ln=True, align='C')
    
    # Save to a temporary file so Streamlit can download it
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name