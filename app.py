from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

from src.db import init_db, fetch_all, fetch_one
from src.auth import authenticate, register_user
from src.validators import validate_registration, validate_dates
from src.services import (
    list_vehicles, calculate_price, vehicle_available, create_booking,
    get_user_bookings, cancel_booking, dashboard_metrics, all_bookings,
    update_booking_status, add_vehicle, update_vehicle, delete_vehicle,
    analytics_rows, popular_vehicles
)
from src.ui import inject_css, hero

st.set_page_config(page_title="Vehicle Rental Platform", page_icon="🚗", layout="wide")
init_db()
inject_css()

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Home"

def logout():
    st.session_state.user = None
    st.session_state.page = "Home"
    st.rerun()

def sidebar():
    with st.sidebar:
        st.title("🚗 RentX")
        if st.session_state.user:
            u = st.session_state.user
            st.success(f"Signed in as\n**{u['name']}**")
            pages = ["Home", "Browse Vehicles", "My Bookings", "Profile"]
            if u["role"] == "admin":
                pages += ["Admin Dashboard", "Manage Vehicles", "Manage Bookings"]
            selected = st.radio("Navigation", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
            st.session_state.page = selected
            st.divider()
            if st.button("Logout", use_container_width=True):
                logout()
        else:
            selected = st.radio("Navigation", ["Home", "Browse Vehicles", "Login", "Register"])
            st.session_state.page = selected
            st.divider()
            st.caption("Demo Admin: admin@rental.local")
            st.caption("Demo Customer: demo@rental.local")

def home():
    hero()
    if not st.session_state.user:
        c1, c2, c3 = st.columns(3)
        c1.metric("🚘 Fleet", "10+")
        c2.metric("📅 Smart Booking", "24/7")
        c3.metric("💳 Transparent", "Pricing")
        st.subheader("Why RentX?")
        cols = st.columns(4)
        for col, title, text in zip(cols,
            ["Real-time availability","Flexible fleet","Secure accounts","Admin analytics"],
            ["Date-overlap validation prevents double booking.",
             "Cars, SUVs, bikes and EVs across multiple locations.",
             "Passwords are stored using bcrypt hashing.",
             "Revenue, bookings and fleet utilization in one dashboard."]):
            with col:
                st.markdown(f"### {title}")
                st.write(text)
        return

    u = st.session_state.user
    if u["role"] == "admin":
        m = dashboard_metrics()
        cols = st.columns(5)
        for col, label, value in zip(cols, ["Vehicles","Available","Customers","Bookings","Revenue"],
                                     [m["vehicles"],m["available"],m["users"],m["bookings"],f"₹{m['revenue']:,.0f}"]):
            col.metric(label, value)
    else:
        bookings = get_user_bookings(u["id"])
        active = [b for b in bookings if b["status"] in ("pending","confirmed")]
        spent = sum(float(b["total"]) for b in bookings if b["status"] != "cancelled")
        c1,c2,c3 = st.columns(3)
        c1.metric("Active Rentals", len(active))
        c2.metric("Total Bookings", len(bookings))
        c3.metric("Total Spend", f"₹{spent:,.0f}")
        st.subheader("Recommended Vehicles")
        show_vehicle_cards(list_vehicles()[:4])

def show_vehicle_cards(rows):
    if not rows:
        st.info("No vehicles match your filters.")
        return
    for start in range(0, len(rows), 3):
        cols = st.columns(3)
        for col, v in zip(cols, rows[start:start+3]):
            with col:
                st.markdown('<div class="vehicle-card">', unsafe_allow_html=True)
                if v["image_url"]:
                    st.image(v["image_url"], use_container_width=True)
                st.markdown(f"### {v['brand']} {v['model']}")
                st.markdown(f'<span class="badge">{v["category"]}</span> &nbsp; {v["year"]}', unsafe_allow_html=True)
                st.write(f"📍 {v['location']} · 👥 {v['seats']} seats · ⚙️ {v['transmission']}")
                st.write(f"⛽ {v['fuel_type']}")
                st.markdown(f'<span class="price">₹{v["daily_rate"]:,.0f}</span> / day', unsafe_allow_html=True)
                if st.button("Book this vehicle", key=f"book_{v['id']}", use_container_width=True):
                    if not st.session_state.user:
                        st.session_state.page = "Login"
                        st.rerun()
                    st.session_state.selected_vehicle = v["id"]
                    st.session_state.page = "Booking"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

def browse():
    st.title("🔎 Browse Vehicles")
    c1,c2,c3,c4 = st.columns(4)
    cats = ["All"] + sorted([r["category"] for r in fetch_all("SELECT DISTINCT category FROM vehicles")])
    locs = ["All"] + sorted([r["location"] for r in fetch_all("SELECT DISTINCT location FROM vehicles")])
    transmissions = ["All","Automatic","Manual"]
    fuels = ["All"] + sorted([r["fuel_type"] for r in fetch_all("SELECT DISTINCT fuel_type FROM vehicles")])
    category = c1.selectbox("Category", cats)
    location = c2.selectbox("Location", locs)
    transmission = c3.selectbox("Transmission", transmissions)
    fuel = c4.selectbox("Fuel", fuels)
    min_rate, max_rate = st.slider("Daily rental range (₹)", 500, 6000, (500, 6000), 100)
    rows = list_vehicles(category, location, min_rate, max_rate, transmission, fuel)
    st.caption(f"{len(rows)} vehicle(s) available")
    show_vehicle_cards(rows)

def booking_page():
    vid = st.session_state.get("selected_vehicle")
    v = fetch_one("SELECT * FROM vehicles WHERE id=?", (vid,))
    if not v:
        st.error("Vehicle not found.")
        return
    st.title(f"📅 Book {v['brand']} {v['model']}")
    left, right = st.columns([1.2,1])
    with left:
        if v["image_url"]: st.image(v["image_url"], use_container_width=True)
        st.write(v["description"])
        st.write(f"**Registration:** {v['registration_no']}")
        st.write(f"**Location:** {v['location']} · **Seats:** {v['seats']}")
    with right:
        pickup = st.date_input("Pickup date", value=date.today()+timedelta(days=1), min_value=date.today())
        ret = st.date_input("Return date", value=date.today()+timedelta(days=3), min_value=date.today()+timedelta(days=1))
        location = st.text_input("Pickup location", value=v["location"])
        payment = st.selectbox("Payment method", ["Pay at pickup","Demo UPI","Demo Card"])
        notes = st.text_area("Special requests", placeholder="Optional")
        err = validate_dates(pickup, ret)
        if err:
            st.warning(err)
        elif not vehicle_available(v["id"], pickup, ret):
            st.error("This vehicle is already booked for the selected dates.")
        else:
            p = calculate_price(v["daily_rate"], pickup, ret, v["deposit"])
            st.markdown("### Price Summary")
            st.write(f"Rental duration: **{p['days']} day(s)**")
            st.write(f"Rental: ₹{p['subtotal']:,.2f}")
            st.write(f"Tax (5%): ₹{p['tax']:,.2f}")
            st.write(f"Security deposit: ₹{p['deposit']:,.2f}")
            st.markdown(f"## Total: ₹{p['total']:,.2f}")
            if st.button("Confirm Booking", type="primary", use_container_width=True):
                ok,msg,_ = create_booking(st.session_state.user["id"],v["id"],pickup,ret,location,payment,notes)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.session_state.page = "My Bookings"
                    st.rerun()

def login():
    st.title("🔐 Login")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In", type="primary")
    if submit:
        user = authenticate(email,password)
        if user:
            st.session_state.user = user
            st.session_state.page = "Admin Dashboard" if user["role"]=="admin" else "Home"
            st.rerun()
        st.error("Invalid email or password.")

def register():
    st.title("📝 Create Account")
    with st.form("register"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        p1 = st.text_input("Password", type="password")
        p2 = st.text_input("Confirm password", type="password")
        submit = st.form_submit_button("Create Account", type="primary")
    if submit:
        errors = validate_registration(name,email,p1,p2,phone)
        if errors:
            for e in errors: st.error(e)
        else:
            ok,msg = register_user(name,email,p1,phone)
            if ok:
                st.success(msg)
                st.session_state.page = "Login"
            else: st.error(msg)

def my_bookings():
    st.title("📋 My Bookings")
    rows = get_user_bookings(st.session_state.user["id"])
    if not rows:
        st.info("You have no bookings yet.")
        return
    df = pd.DataFrame([dict(r) for r in rows])
    display_cols = ["booking_code","brand","model","pickup_date","return_date","total","status"]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
    for b in rows:
        with st.expander(f"{b['booking_code']} · {b['brand']} {b['model']} · {b['status'].upper()}"):
            a,bcol,c = st.columns(3)
            a.write(f"**Pickup:** {b['pickup_date']}")
            bcol.write(f"**Return:** {b['return_date']}")
            c.write(f"**Total:** ₹{b['total']:,.2f}")
            st.write(f"Payment: {b['payment_method']} · Location: {b['pickup_location']}")
            if b["status"] in ("pending","confirmed") and b["pickup_date"] > date.today().isoformat():
                if st.button("Cancel booking", key=f"cancel_{b['id']}"):
                    ok,msg = cancel_booking(b["id"],st.session_state.user["id"])
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()

def profile():
    st.title("👤 Profile")
    u = fetch_one("SELECT * FROM users WHERE id=?", (st.session_state.user["id"],))
    c1,c2 = st.columns(2)
    c1.text_input("Name", u["name"], disabled=True)
    c1.text_input("Email", u["email"], disabled=True)
    c2.text_input("Phone", u["phone"], disabled=True)
    c2.text_input("Role", u["role"].title(), disabled=True)
    st.caption(f"Member since: {u['created_at']}")

def admin_dashboard():
    st.title("📊 Admin Dashboard")
    m = dashboard_metrics()
    cols=st.columns(5)
    for col,label,value in zip(cols,["Vehicles","Available","Customers","Bookings","Revenue"],
                              [m["vehicles"],m["available"],m["users"],m["bookings"],f"₹{m['revenue']:,.0f}"]):
        col.metric(label,value)
    st.divider()
    rows = analytics_rows()
    if rows:
        df=pd.DataFrame([dict(r) for r in rows])
        c1,c2=st.columns(2)
        with c1:
            st.subheader("Revenue Trend")
            st.plotly_chart(px.line(df,x="day",y="revenue",markers=True),use_container_width=True)
        with c2:
            st.subheader("Bookings Trend")
            st.plotly_chart(px.bar(df,x="day",y="bookings"),use_container_width=True)
    popular=popular_vehicles()
    if popular:
        st.subheader("Fleet Performance")
        st.dataframe(pd.DataFrame([dict(r) for r in popular]),use_container_width=True,hide_index=True)

def manage_vehicles():
    st.title("🚘 Manage Vehicles")
    tab1,tab2 = st.tabs(["Add Vehicle","Fleet"])
    with tab1:
        with st.form("add_vehicle"):
            c1,c2,c3=st.columns(3)
            reg=c1.text_input("Registration *")
            brand=c2.text_input("Brand *")
            model=c3.text_input("Model *")
            category=c1.selectbox("Category",["Hatchback","Sedan","SUV","EV","Bike","Luxury"])
            year=c2.number_input("Year",2000,2035,2025)
            seats=c3.number_input("Seats",1,12,5)
            trans=c1.selectbox("Transmission",["Automatic","Manual"])
            fuel=c2.selectbox("Fuel",["Petrol","Diesel","Electric","CNG"])
            location=c3.text_input("Location","Ongole")
            rate=c1.number_input("Daily rate",100.0,100000.0,2000.0,100.0)
            deposit=c2.number_input("Security deposit",0.0,100000.0,3000.0,100.0)
            status=c3.selectbox("Status",["available","maintenance","inactive"])
            image=c1.text_input("Image URL")
            desc=st.text_area("Description")
            submit=st.form_submit_button("Add Vehicle",type="primary")
        if submit:
            if not reg.strip() or not brand.strip() or not model.strip():
                st.error("Registration, brand and model are required.")
            else:
                try:
                    add_vehicle(dict(registration_no=reg.strip(),brand=brand.strip(),model=model.strip(),
                        category=category,year=int(year),seats=int(seats),transmission=trans,
                        fuel_type=fuel,location=location.strip(),daily_rate=float(rate),deposit=float(deposit),
                        status=status,image_url=image.strip(),description=desc.strip()))
                    st.success("Vehicle added.")
                    st.rerun()
                except Exception as e: st.error(f"Could not add vehicle: {e}")
    with tab2:
        rows=fetch_all("SELECT * FROM vehicles ORDER BY id DESC")
        df=pd.DataFrame([dict(r) for r in rows])
        st.dataframe(df[["id","registration_no","brand","model","category","location","daily_rate","status"]],
                     use_container_width=True,hide_index=True)
        vid=st.selectbox("Select vehicle", [r["id"] for r in rows])
        v=fetch_one("SELECT * FROM vehicles WHERE id=?",(vid,))
        with st.form("edit_vehicle"):
            c1,c2,c3=st.columns(3)
            reg=c1.text_input("Registration",v["registration_no"])
            brand=c2.text_input("Brand",v["brand"])
            model=c3.text_input("Model",v["model"])
            category=c1.selectbox("Category",["Hatchback","Sedan","SUV","EV","Bike","Luxury"],index=["Hatchback","Sedan","SUV","EV","Bike","Luxury"].index(v["category"]) if v["category"] in ["Hatchback","Sedan","SUV","EV","Bike","Luxury"] else 0)
            year=c2.number_input("Year",2000,2035,v["year"])
            seats=c3.number_input("Seats",1,12,v["seats"])
            trans=c1.selectbox("Transmission",["Automatic","Manual"],index=0 if v["transmission"]=="Automatic" else 1)
            fuel=c2.selectbox("Fuel",["Petrol","Diesel","Electric","CNG"],index=["Petrol","Diesel","Electric","CNG"].index(v["fuel_type"]) if v["fuel_type"] in ["Petrol","Diesel","Electric","CNG"] else 0)
            location=c3.text_input("Location",v["location"])
            rate=c1.number_input("Daily rate",100.0,100000.0,float(v["daily_rate"]),100.0)
            deposit=c2.number_input("Security deposit",0.0,100000.0,float(v["deposit"]),100.0)
            status=c3.selectbox("Status",["available","maintenance","inactive"],index=["available","maintenance","inactive"].index(v["status"]))
            image=c1.text_input("Image URL",v["image_url"])
            desc=st.text_area("Description",v["description"])
            save=st.form_submit_button("Save Changes",type="primary")
        if save:
            try:
                update_vehicle(vid,dict(registration_no=reg,brand=brand,model=model,category=category,
                    year=int(year),seats=int(seats),transmission=trans,fuel_type=fuel,location=location,
                    daily_rate=float(rate),deposit=float(deposit),status=status,image_url=image,description=desc))
                st.success("Vehicle updated.")
                st.rerun()
            except Exception as e: st.error(str(e))
        if st.button("Delete selected vehicle"):
            ok,msg=delete_vehicle(vid)
            (st.success if ok else st.error)(msg)
            if ok: st.rerun()

def manage_bookings():
    st.title("🧾 Manage Bookings")
    rows=all_bookings()
    if not rows: st.info("No bookings yet."); return
    df=pd.DataFrame([dict(r) for r in rows])
    st.download_button("⬇️ Export CSV",df.to_csv(index=False).encode(),"bookings.csv","text/csv")
    st.dataframe(df[["id","booking_code","customer_name","brand","model","pickup_date","return_date","total","status"]],
                 use_container_width=True,hide_index=True)
    bid=st.selectbox("Booking ID",df["id"].tolist())
    current=fetch_one("SELECT status FROM bookings WHERE id=?",(bid,))["status"]
    new=st.selectbox("New status",["pending","confirmed","completed","cancelled"],
                     index=["pending","confirmed","completed","cancelled"].index(current))
    if st.button("Update status",type="primary"):
        update_booking_status(bid,new); st.success("Booking status updated."); st.rerun()

def app_router():
    sidebar()
    page=st.session_state.page
    if page=="Home": home()
    elif page=="Browse Vehicles": browse()
    elif page=="Login": login()
    elif page=="Register": register()
    elif page=="Booking": booking_page()
    elif page=="My Bookings": my_bookings()
    elif page=="Profile": profile()
    elif page=="Admin Dashboard": admin_dashboard()
    elif page=="Manage Vehicles": manage_vehicles()
    elif page=="Manage Bookings": manage_bookings()

if __name__ == "__main__":
    app_router()
