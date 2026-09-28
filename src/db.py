from pathlib import Path
import sqlite3
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "rental.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT DEFAULT '',
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('customer','admin')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_no TEXT NOT NULL UNIQUE,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    category TEXT NOT NULL,
    year INTEGER NOT NULL,
    seats INTEGER NOT NULL,
    transmission TEXT NOT NULL,
    fuel_type TEXT NOT NULL,
    location TEXT NOT NULL,
    daily_rate REAL NOT NULL,
    deposit REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'available'
        CHECK(status IN ('available','maintenance','inactive')),
    image_url TEXT DEFAULT '',
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_code TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    pickup_date TEXT NOT NULL,
    return_date TEXT NOT NULL,
    pickup_location TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    subtotal REAL NOT NULL,
    tax REAL NOT NULL,
    deposit REAL NOT NULL,
    total REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed'
        CHECK(status IN ('pending','confirmed','completed','cancelled')),
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bookings_vehicle_dates
ON bookings(vehicle_id, pickup_date, return_date);

CREATE INDEX IF NOT EXISTS idx_bookings_user
ON bookings(user_id);
"""

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)

def fetch_all(query, params=()):
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()

def fetch_one(query, params=()):
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()

def execute(query, params=()):
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid
