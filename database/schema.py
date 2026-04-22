# database/schema.py
from database.db import execute

def init_tables():
    execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        phone TEXT UNIQUE,
        password TEXT,
        is_registered INTEGER DEFAULT 0
    )""")

    execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        phone TEXT UNIQUE,
        password TEXT,
        is_available INTEGER DEFAULT 1,
        last_lat REAL DEFAULT 0.0,
        last_lng REAL DEFAULT 0.0,
        status TEXT DEFAULT 'active'
    )""")

    execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        phone TEXT,
        commission_rate REAL DEFAULT 15.0,
        status TEXT DEFAULT 'active'
    )""")

    execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        phone TEXT,
        pickup_location TEXT,
        pickup_lat REAL DEFAULT 0.0,
        pickup_lng REAL DEFAULT 0.0,
        urgency TEXT DEFAULT 'normal',
        oxygen_needed INTEGER DEFAULT 0,
        icu_needed INTEGER DEFAULT 0,
        nurse_needed INTEGER DEFAULT 0,
        patient_note TEXT,
        discount_applied REAL DEFAULT 0.0,
        payment_status TEXT DEFAULT 'pending',
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER,
        driver_id INTEGER,
        supplier_id INTEGER,
        trip_source TEXT,
        trip_status TEXT DEFAULT 'assigned',
        fare_amount REAL DEFAULT 0.0,
        is_fare_accepted INTEGER DEFAULT 0,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )""")

    execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")

    # --- Indexes for fast lookups on frequently queried columns ---
    # Bookings: looked up by phone and status constantly
    execute("CREATE INDEX IF NOT EXISTS idx_bookings_phone ON bookings (phone)")
    execute("CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings (status)")
    execute("CREATE INDEX IF NOT EXISTS idx_bookings_phone_status ON bookings (phone, status)")

    # Trips: joined against booking_id and driver_id on nearly every query
    execute("CREATE INDEX IF NOT EXISTS idx_trips_booking_id ON trips (booking_id)")
    execute("CREATE INDEX IF NOT EXISTS idx_trips_driver_id ON trips (driver_id)")
    execute("CREATE INDEX IF NOT EXISTS idx_trips_trip_status ON trips (trip_status)")

    # Drivers: filtered by availability and status for dispatch
    execute("CREATE INDEX IF NOT EXISTS idx_drivers_available ON drivers (is_available, status)")
