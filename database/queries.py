# database/queries.py
from database.db import execute, fetch_one, fetch_all
from werkzeug.security import generate_password_hash, check_password_hash
import requests

# --- CONFIGURATION ---
# Replace with your actual Google Maps API Key before launch
GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY_HERE"

def get_coordinates(address):
    """Converts a text address into real GPS coordinates using Google Maps."""
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
        print("Warning: Google Maps API Key not set.")
        return None, None

    try:
        # Standardizing the search to Bangladesh for accuracy
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address},+Bangladesh&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data['status'] == 'OK':
            lat = data['results'][0]['geometry']['location']['lat']
            lng = data['results'][0]['geometry']['location']['lng']
            return lat, lng
        else:
            print(f"Geocoding failed with status: {data['status']}")

    except Exception as e:
        print(f"Geocoding error: {e}")

    return None, None


# --- CUSTOMER & BOOKING LOGIC ---
def create_booking(name, phone, pickup, urgency, oxygen, icu, nurse, note):
    customer = fetch_one("SELECT is_registered FROM customers WHERE phone = ?", (phone,))
    discount = 10.0 if (customer and customer['is_registered'] == 1) else 0.0

    existing = fetch_one("SELECT id FROM bookings WHERE phone = ? AND status = 'pending'", (phone,))
    if existing:
        return False, "An active emergency request is already being processed for this number."

    lat, lng = get_coordinates(pickup)

    if lat is None or lng is None:
        return False, "Unable to verify the pickup location exactly. Please provide a more precise address or landmark."

    execute(
        """INSERT INTO bookings (
            customer_name, phone, pickup_location, pickup_lat, pickup_lng, urgency,
            oxygen_needed, icu_needed, nurse_needed, patient_note, discount_applied
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, phone, pickup, lat, lng, urgency, oxygen, icu, nurse, note, discount)
    )
    booking = fetch_one("SELECT * FROM bookings WHERE phone = ? ORDER BY id DESC", (phone,))
    if booking is None:
        return False, "Booking was created but could not be retrieved. Please try again."
    return True, booking

def register_customer(name, phone, password):
    """Enables permanent discount and creates a secure login."""
    existing = fetch_one("SELECT id FROM customers WHERE phone = ?", (phone,))
    if existing:
        return False, "This phone number is already registered."

    hashed_password = generate_password_hash(password)
    execute(
        "INSERT INTO customers (full_name, phone, password, is_registered) VALUES (?, ?, ?, 1)",
        (name, phone, hashed_password)
    )
    return True, "Account Created! You can now log in securely."

def verify_login(role, identifier, password):
    """Universal authentication gateway. All passwords must be hashed (werkzeug)."""
    if role == 'Manager':
        user = fetch_one("SELECT * FROM admins WHERE username = ?", (identifier,))
    elif role == 'Driver':
        user = fetch_one("SELECT * FROM drivers WHERE phone = ?", (identifier,))
    elif role == 'Customer':
        user = fetch_one("SELECT * FROM customers WHERE phone = ?", (identifier,))
    else:
        return False, None

    if user and user.get('password'):
        if check_password_hash(user['password'], password):
            return True, user

    return False, None

def cancel_booking_by_customer(booking_id):
    execute("UPDATE bookings SET status = 'cancelled_by_customer' WHERE id = ?", (booking_id,))
    # Best-effort: free up the driver and mark the trip rejected if one was assigned.
    # These are non-critical — silently skip if no trip exists yet.
    try:
        execute("""
            UPDATE drivers SET is_available = 1
            WHERE id = (SELECT driver_id FROM trips WHERE booking_id = ? LIMIT 1)
        """, (booking_id,))
        execute("UPDATE trips SET trip_status = 'rejected' WHERE booking_id = ?", (booking_id,))
    except Exception as e:
        print(f"[cancel_booking] Non-critical cleanup error for booking {booking_id}: {e}")
    return True


# --- DISPATCH & FLEET LOGIC ---
def get_all_drivers():
    return fetch_all("SELECT * FROM drivers")

def get_pending_bookings():
    return fetch_all("SELECT * FROM bookings WHERE status = 'pending' ORDER BY id DESC")

def get_available_sina_drivers():
    return fetch_all("SELECT * FROM drivers WHERE is_available = 1 AND status = 'active'")

def get_all_suppliers():
    return fetch_all("SELECT * FROM suppliers WHERE status = 'active'")

def dispatch_mission(booking_id, source, driver_id=None, supplier_id=None):
    execute("UPDATE bookings SET status = 'assigned' WHERE id = ?", (booking_id,))
    if source == 'sina':
        execute("UPDATE drivers SET is_available = 0 WHERE id = ?", (driver_id,))
        execute(
            "INSERT INTO trips (booking_id, driver_id, trip_source) VALUES (?, ?, 'sina')",
            (booking_id, driver_id)
        )
    else:
        execute(
            "INSERT INTO trips (booking_id, supplier_id, trip_source) VALUES (?, ?, 'external')",
            (booking_id, supplier_id)
        )
    return True

def get_live_map_data():
    drivers = fetch_all(
        "SELECT full_name, is_available, last_lat, last_lng FROM drivers WHERE last_lat != 0.0"
    )
    pending = fetch_all(
        "SELECT customer_name, urgency, pickup_lat, pickup_lng FROM bookings WHERE status = 'pending' AND pickup_lat != 0.0"
    )
    active_trips = fetch_all("""
        SELECT d.full_name as driver_name, d.last_lat, d.last_lng, b.pickup_lat, b.pickup_lng
        FROM trips t
        JOIN drivers d ON t.driver_id = d.id
        JOIN bookings b ON t.booking_id = b.id
        WHERE t.trip_status NOT IN ('completed', 'rejected') AND d.last_lat != 0.0
    """)
    return drivers, pending, active_trips


# --- TRIP PROGRESS & DRIVER ACTIONS ---
def get_assigned_trip_for_driver(driver_id):
    return fetch_one("""
        SELECT t.id as trip_id, b.*, t.trip_status FROM trips t
        JOIN bookings b ON t.booking_id = b.id
        WHERE t.driver_id = ? AND t.trip_status NOT IN ('completed', 'rejected')
        ORDER BY t.id DESC LIMIT 1
    """, (driver_id,))

def update_trip_status(trip_id, status, driver_id=None):
    execute("UPDATE trips SET trip_status = ? WHERE id = ?", (status, trip_id))
    if status in ['completed', 'rejected'] and driver_id is not None:
        execute("UPDATE drivers SET is_available = 1 WHERE id = ?", (driver_id,))
    if status == 'completed':
        execute("UPDATE trips SET completed_at = CURRENT_TIMESTAMP WHERE id = ?", (trip_id,))

def get_customer_active_status(phone):
    return fetch_one("""
        SELECT
            b.id as booking_id, b.status as booking_status, b.pickup_location,
            b.pickup_lat, b.pickup_lng, b.discount_applied,
            t.id as trip_id, t.trip_status, t.trip_source, t.fare_amount, t.is_fare_accepted,
            d.full_name as driver_name, d.phone as driver_phone, d.last_lat, d.last_lng,
            s.company_name as supplier_name, s.phone as supplier_phone
        FROM bookings b
        LEFT JOIN trips t ON b.id = t.booking_id
        LEFT JOIN drivers d ON t.driver_id = d.id
        LEFT JOIN suppliers s ON t.supplier_id = s.id
        WHERE b.phone = ?
          AND b.status != 'completed'
          AND b.status != 'cancelled_by_customer'
        ORDER BY b.id DESC LIMIT 1
    """, (phone,))


# --- FINANCE & PAYMENTS ---
def accept_trip_fare(trip_id):
    execute("UPDATE trips SET is_fare_accepted = 1 WHERE id = ?", (trip_id,))
    return True

def get_completed_missions():
    return fetch_all("""
        SELECT t.*, b.customer_name, b.discount_applied, b.payment_status,
               b.id as b_id, s.company_name, s.commission_rate
        FROM trips t
        JOIN bookings b ON t.booking_id = b.id
        LEFT JOIN suppliers s ON t.supplier_id = s.id
        WHERE t.trip_status = 'completed'
        ORDER BY t.id DESC
    """)

def finalize_finance(trip_id, fare, b_id, pay_status):
    execute("UPDATE trips SET fare_amount = ? WHERE id = ?", (fare, trip_id))
    execute("UPDATE bookings SET payment_status = ? WHERE id = ?", (pay_status, b_id))

def get_unpaid_bills_for_customer(phone):
    return fetch_all("""
        SELECT t.id as trip_id, t.fare_amount, t.completed_at,
               b.id as booking_id, b.discount_applied, b.payment_status, b.pickup_location
        FROM trips t
        JOIN bookings b ON t.booking_id = b.id
        WHERE b.phone = ? AND t.trip_status = 'completed' AND b.payment_status != 'paid'
        ORDER BY t.id DESC
    """, (phone,))

def process_customer_payment(booking_id, payment_method):
    execute("UPDATE bookings SET payment_status = 'paid' WHERE id = ?", (booking_id,))
    return True, f"Payment successfully processed via {payment_method}."

def get_driver_pending_collections(driver_id):
    return fetch_all("""
        SELECT t.id as trip_id, t.fare_amount,
               b.id as booking_id, b.customer_name, b.payment_status, b.discount_applied
        FROM trips t
        JOIN bookings b ON t.booking_id = b.id
        WHERE t.driver_id = ? AND t.trip_status = 'completed' AND b.payment_status != 'paid'
    """, (driver_id,))

def driver_confirm_cash_payment(booking_id, trip_id):
    execute("UPDATE bookings SET payment_status = 'paid' WHERE id = ?", (booking_id,))
    return True


# --- HR & STAFF MANAGEMENT ---
def register_driver(name, phone, password):
    existing = fetch_one("SELECT id FROM drivers WHERE phone = ?", (phone,))
    if existing:
        return False, "A driver with this phone number already exists."

    hashed_password = generate_password_hash(password)
    execute(
        "INSERT INTO drivers (full_name, phone, password) VALUES (?, ?, ?)",
        (name, phone, hashed_password)
    )
    return True, f"Driver {name} successfully registered and ready for dispatch."

def register_admin(username, password):
    existing = fetch_one("SELECT id FROM admins WHERE username = ?", (username,))
    if existing:
        return False, "This Admin username is already taken."

    hashed_password = generate_password_hash(password)
    execute(
        "INSERT INTO admins (username, password) VALUES (?, ?)",
        (username, hashed_password)
    )
    return True, f"Manager '{username}' successfully registered."

def get_paid_bills_for_customer(phone):
    return fetch_all("""
        SELECT t.id as trip_id, t.fare_amount, t.completed_at,
               b.id as booking_id, b.discount_applied, b.payment_status,
               b.pickup_location
        FROM trips t
        JOIN bookings b ON t.booking_id = b.id
        WHERE b.phone = ? AND b.payment_status = 'paid'
        ORDER BY t.id DESC
    """, (phone,))
