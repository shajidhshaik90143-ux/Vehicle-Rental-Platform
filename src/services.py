from datetime import date, timedelta
from .db import fetch_all, fetch_one, execute

TAX_RATE = 0.05

def list_vehicles(category=None, location=None, min_rate=None, max_rate=None,
                  transmission=None, fuel=None, status="available"):
    query = "SELECT * FROM vehicles WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if location and location != "All":
        query += " AND location = ?"
        params.append(location)
    if min_rate is not None:
        query += " AND daily_rate >= ?"
        params.append(min_rate)
    if max_rate is not None:
        query += " AND daily_rate <= ?"
        params.append(max_rate)
    if transmission and transmission != "All":
        query += " AND transmission = ?"
        params.append(transmission)
    if fuel and fuel != "All":
        query += " AND fuel_type = ?"
        params.append(fuel)
    query += " ORDER BY daily_rate ASC, brand ASC"
    return fetch_all(query, params)

def vehicle_available(vehicle_id, pickup_date, return_date, exclude_booking_id=None):
    query = """
    SELECT id FROM bookings
    WHERE vehicle_id = ?
      AND status IN ('pending','confirmed')
      AND pickup_date < ?
      AND return_date > ?
    """
    params = [vehicle_id, return_date.isoformat(), pickup_date.isoformat()]
    if exclude_booking_id:
        query += " AND id != ?"
        params.append(exclude_booking_id)
    return fetch_one(query, params) is None

def calculate_price(daily_rate, pickup_date, return_date, deposit):
    days = max(1, (return_date - pickup_date).days)
    subtotal = daily_rate * days
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax + deposit, 2)
    return {
        "days": days,
        "subtotal": round(subtotal, 2),
        "tax": tax,
        "deposit": round(deposit, 2),
        "total": total,
    }

def create_booking(user_id, vehicle_id, pickup_date, return_date,
                   pickup_location, payment_method, notes=""):
    vehicle = fetch_one("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    if not vehicle:
        return False, "Vehicle not found.", None
    if vehicle["status"] != "available":
        return False, "This vehicle is not currently available.", None
    if not vehicle_available(vehicle_id, pickup_date, return_date):
        return False, "Vehicle is already booked for an overlapping period.", None

    pricing = calculate_price(vehicle["daily_rate"], pickup_date, return_date, vehicle["deposit"])
    code = f"VR-{date.today().strftime('%y%m%d')}-{vehicle_id:03d}-{user_id:03d}-{int(pickup_date.strftime('%d')):02d}"
    existing = fetch_one("SELECT id FROM bookings WHERE booking_code = ?", (code,))
    if existing:
        code += f"-{existing['id']}"

    booking_id = execute("""
        INSERT INTO bookings(
            booking_code,user_id,vehicle_id,pickup_date,return_date,
            pickup_location,payment_method,subtotal,tax,deposit,total,status,notes
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        code, user_id, vehicle_id, pickup_date.isoformat(), return_date.isoformat(),
        pickup_location, payment_method, pricing["subtotal"], pricing["tax"],
        pricing["deposit"], pricing["total"], "confirmed", notes.strip()
    ))
    return True, "Booking confirmed.", booking_id

def get_user_bookings(user_id):
    return fetch_all("""
        SELECT b.*, v.brand, v.model, v.registration_no, v.category
        FROM bookings b JOIN vehicles v ON v.id=b.vehicle_id
        WHERE b.user_id=?
        ORDER BY b.created_at DESC
    """, (user_id,))

def cancel_booking(booking_id, user_id):
    booking = fetch_one(
        "SELECT * FROM bookings WHERE id=? AND user_id=?",
        (booking_id, user_id)
    )
    if not booking:
        return False, "Booking not found."
    if booking["status"] in ("cancelled", "completed"):
        return False, "This booking cannot be cancelled."
    if booking["pickup_date"] <= date.today().isoformat():
        return False, "Bookings starting today or earlier cannot be cancelled."
    execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
    return True, "Booking cancelled."

def dashboard_metrics():
    total_vehicles = fetch_one("SELECT COUNT(*) c FROM vehicles")["c"]
    available = fetch_one("SELECT COUNT(*) c FROM vehicles WHERE status='available'")["c"]
    users = fetch_one("SELECT COUNT(*) c FROM users WHERE role='customer'")["c"]
    bookings = fetch_one("SELECT COUNT(*) c FROM bookings")["c"]
    revenue = fetch_one(
        "SELECT COALESCE(SUM(total),0) total FROM bookings WHERE status IN ('confirmed','completed')"
    )["total"]
    return {
        "vehicles": total_vehicles, "available": available, "users": users,
        "bookings": bookings, "revenue": float(revenue or 0)
    }

def all_bookings():
    return fetch_all("""
        SELECT b.*, u.name customer_name, u.email,
               v.brand, v.model, v.registration_no
        FROM bookings b
        JOIN users u ON u.id=b.user_id
        JOIN vehicles v ON v.id=b.vehicle_id
        ORDER BY b.created_at DESC
    """)

def update_booking_status(booking_id, status):
    allowed = {"pending","confirmed","completed","cancelled"}
    if status not in allowed:
        return False
    execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
    return True

def add_vehicle(data):
    return execute("""
        INSERT INTO vehicles(
            registration_no,brand,model,category,year,seats,transmission,
            fuel_type,location,daily_rate,deposit,status,image_url,description
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, tuple(data[k] for k in (
        "registration_no","brand","model","category","year","seats",
        "transmission","fuel_type","location","daily_rate","deposit",
        "status","image_url","description"
    )))

def update_vehicle(vehicle_id, data):
    execute("""
        UPDATE vehicles SET registration_no=?,brand=?,model=?,category=?,year=?,
        seats=?,transmission=?,fuel_type=?,location=?,daily_rate=?,deposit=?,
        status=?,image_url=?,description=? WHERE id=?
    """, tuple(data[k] for k in (
        "registration_no","brand","model","category","year","seats",
        "transmission","fuel_type","location","daily_rate","deposit",
        "status","image_url","description"
    )) + (vehicle_id,))

def delete_vehicle(vehicle_id):
    active = fetch_one("""
        SELECT COUNT(*) c FROM bookings
        WHERE vehicle_id=? AND status IN ('pending','confirmed')
    """, (vehicle_id,))["c"]
    if active:
        return False, "Cannot delete a vehicle with active bookings."
    execute("DELETE FROM vehicles WHERE id=?", (vehicle_id,))
    return True, "Vehicle deleted."

def analytics_rows():
    return fetch_all("""
        SELECT date(created_at) day, COUNT(*) bookings,
               ROUND(COALESCE(SUM(total),0),2) revenue
        FROM bookings
        WHERE status IN ('confirmed','completed')
        GROUP BY date(created_at)
        ORDER BY day
    """)

def popular_vehicles():
    return fetch_all("""
        SELECT v.brand || ' ' || v.model vehicle,
               COUNT(b.id) bookings,
               ROUND(COALESCE(SUM(b.total),0),2) revenue
        FROM vehicles v
        LEFT JOIN bookings b ON b.vehicle_id=v.id AND b.status IN ('confirmed','completed')
        GROUP BY v.id
        ORDER BY bookings DESC, revenue DESC
        LIMIT 10
    """)
