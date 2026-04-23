# utils/location_loader.py
import sqlite3

LOCATION_DB_PATH = "database/bangladesh_locations_seed.sqlite"

# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _get_conn():
    """Open a connection to the location seed database."""
    conn = sqlite3.connect(LOCATION_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Dropdown data loaders  (used by Streamlit pages for cascading selects)
# ---------------------------------------------------------------------------

def get_divisions():
    """Return all divisions ordered by English name."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name_en, name_bn FROM divisions ORDER BY name_en")
        return cursor.fetchall()
    finally:
        conn.close()


def get_districts(division_id):
    """Return all districts belonging to a division, ordered by English name."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name_en, name_bn FROM districts WHERE division_id = ? ORDER BY name_en",
            (division_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_upazilas(district_id):
    """Return all upazilas belonging to a district, ordered by English name."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name_en, name_bn FROM upazilas WHERE district_id = ? ORDER BY name_en",
            (district_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_unions(upazila_id):
    """Return all unions belonging to an upazila, ordered by English name."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name_en, name_bn FROM unions WHERE upazila_id = ? ORDER BY name_en",
            (upazila_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def is_valid_location_chain(division_name, district_name, upazila_name):
    """
    Returns True if the given division → district → upazila chain exists in
    the database (matched on English names, case-insensitive).
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id
            FROM upazilas u
            JOIN districts d  ON u.district_id  = d.id
            JOIN divisions  v ON d.division_id   = v.id
            WHERE LOWER(v.name_en) = LOWER(?)
              AND LOWER(d.name_en) = LOWER(?)
              AND LOWER(u.name_en) = LOWER(?)
            LIMIT 1
        """, (division_name, district_name, upazila_name))
        row = cursor.fetchone()
        return row is not None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Coordinate lookup  (used by queries.py offline fallback)
# ---------------------------------------------------------------------------

def get_district_coordinates(district_name_query: str):
    """
    Try to find GPS coordinates for a district by matching the query string
    against both English and Bengali district names (case-insensitive substring
    match).

    Returns (lat, lng) if found, or (None, None) if not.

    Only districts have lat/lon in this dataset. Upazilas and unions do not,
    so callers should use this for the offline fallback.
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        # Exact English name match first (fastest)
        cursor.execute(
            "SELECT lat, lon FROM districts WHERE LOWER(name_en) = LOWER(?) LIMIT 1",
            (district_name_query.strip(),)
        )
        row = cursor.fetchone()
        if row and row["lat"] is not None:
            return float(row["lat"]), float(row["lon"])

        # Substring match — English name contained in the query string
        cursor.execute("SELECT name_en, name_bn, lat, lon FROM districts")
        all_districts = cursor.fetchall()
        query_lower = district_name_query.lower()
        for d in all_districts:
            en = (d["name_en"] or "").lower()
            bn = (d["name_bn"] or "")
            if (en and en in query_lower) or (bn and bn in district_name_query):
                if d["lat"] is not None:
                    return float(d["lat"]), float(d["lon"])

        return None, None
    finally:
        conn.close()


def get_coordinates_for_address(address: str):
    """
    Best-effort offline coordinate resolver for a free-text address string.

    Search priority:
      1. District name (English) — exact match
      2. District name (English) — substring match inside address
      3. District name (Bengali) — substring match inside address
      4. Division name (English) — substring match (very rough, last resort)

    Returns (lat, lng) on success, or (None, None) if nothing matched.
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        address_lower = address.lower()

        # --- Step 1 & 2: try districts (they have real lat/lon) ---
        cursor.execute("SELECT name_en, name_bn, lat, lon FROM districts")
        districts = cursor.fetchall()

        # Exact English match
        for d in districts:
            if d["name_en"] and d["name_en"].lower() == address_lower:
                if d["lat"] is not None:
                    return float(d["lat"]), float(d["lon"])

        # Substring English / Bengali match
        for d in districts:
            en = (d["name_en"] or "").lower()
            bn = (d["name_bn"] or "")
            if (en and en in address_lower) or (bn and bn in address):
                if d["lat"] is not None:
                    return float(d["lat"]), float(d["lon"])

        # --- Step 3: fall back to division centre (rough) ---
        # Divisions don't have lat/lon in the DB, but we can derive it from
        # the average of their districts.
        cursor.execute("""
            SELECT v.name_en, v.name_bn, AVG(d.lat) as avg_lat, AVG(d.lon) as avg_lon
            FROM divisions v
            JOIN districts d ON d.division_id = v.id
            WHERE d.lat IS NOT NULL
            GROUP BY v.id
        """)
        divisions = cursor.fetchall()
        for v in divisions:
            en = (v["name_en"] or "").lower()
            bn = (v["name_bn"] or "")
            if (en and en in address_lower) or (bn and bn in address):
                if v["avg_lat"] is not None:
                    return float(v["avg_lat"]), float(v["avg_lon"])

        return None, None
    finally:
        conn.close()

