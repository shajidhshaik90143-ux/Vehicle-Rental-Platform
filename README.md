# Vehicle Rental Platform

A strong portfolio-ready vehicle rental management platform built with Python, Streamlit and SQLite.

## Features

### Customer
- Registration and secure password hashing
- Login/logout
- Vehicle search and filtering
- Vehicle detail cards
- Date-based availability checking
- Dynamic rental pricing
- Booking creation and cancellation
- Booking history
- Profile management
- Dashboard with spending and rental statistics

### Admin
- Admin dashboard with KPIs
- Vehicle CRUD management
- Booking management
- User overview
- Revenue and fleet analytics
- Booking status updates
- Seed/demo data

### Engineering
- SQLite database with normalized tables
- Password hashing with bcrypt
- Parameterized SQL queries
- Date-overlap booking validation
- Modular architecture
- Session-state authentication
- Input validation
- CSV export
- Responsive Streamlit UI

## Demo accounts

Admin:
- Email: admin@rental.local
- Password: Admin@123

Customer:
- Email: demo@rental.local
- Password: Demo@123

## Run on Windows

```cmd
cd Vehicle_Rental_Platform
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py
streamlit run app.py
```

If `python` is not recognized, try `py`.

## Run on Linux/macOS

```bash
cd Vehicle_Rental_Platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
streamlit run app.py
```

## Database

The SQLite database is created at:
`data/rental.db`

To reset the demo database:

```cmd
python seed.py --reset
```

## Project structure

```text
Vehicle_Rental_Platform/
├── app.py
├── seed.py
├── requirements.txt
├── README.md
├── data/
│   └── rental.db                 # generated
├── src/
│   ├── __init__.py
│   ├── auth.py
│   ├── db.py
│   ├── services.py
│   ├── ui.py
│   └── validators.py
└── assets/
```

## Notes

Payments are represented as a safe demo workflow; no real payment gateway is connected. For production deployment, add a real payment provider, HTTPS, CSRF protections where applicable, email verification, rate limiting, audit logs, and a production database.
