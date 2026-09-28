import sys
from src.db import init_db, get_conn
from src.auth import hash_password

def seed(reset=False):
    init_db()
    with get_conn() as conn:
        if reset:
            conn.executescript("""
                DELETE FROM bookings;
                DELETE FROM vehicles;
                DELETE FROM users;
                DELETE FROM sqlite_sequence WHERE name IN ('bookings','vehicles','users');
            """)

        conn.execute("""
            INSERT OR IGNORE INTO users(name,email,phone,password_hash,role)
            VALUES(?,?,?,?,?)
        """, ("Platform Admin","admin@rental.local","9876543210",hash_password("Admin@123"),"admin"))

        conn.execute("""
            INSERT OR IGNORE INTO users(name,email,phone,password_hash,role)
            VALUES(?,?,?,?,?)
        """, ("Demo Customer","demo@rental.local","9123456789",hash_password("Demo@123"),"customer"))

        vehicles = [
            ("AP-01-AB-1010","Toyota","Innova Crysta","SUV",2024,7,"Automatic","Diesel","Vijayawada",3200,5000,"available","https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=900&q=80","Spacious family SUV with premium comfort and luggage capacity."),
            ("AP-02-CD-2020","Hyundai","Creta","SUV",2025,5,"Automatic","Petrol","Guntur",2400,4000,"available","https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=900&q=80","Modern compact SUV suited for city and highway travel."),
            ("AP-03-EF-3030","Maruti","Swift","Hatchback",2024,5,"Manual","Petrol","Ongole",1500,2500,"available","https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=900&q=80","Fuel-efficient hatchback for economical daily rentals."),
            ("AP-04-GH-4040","Honda","City","Sedan",2023,5,"Automatic","Petrol","Vijayawada",2200,3500,"available","https://images.unsplash.com/photo-1553440569-bcc63803a83d?auto=format&fit=crop&w=900&q=80","Comfortable sedan with a refined cabin and smooth automatic drive."),
            ("AP-05-IJ-5050","Kia","Seltos","SUV",2024,5,"Automatic","Diesel","Guntur",2800,4500,"available","https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=900&q=80","Feature-rich SUV with excellent highway comfort."),
            ("AP-06-KL-6060","Tata","Nexon EV","EV",2025,5,"Automatic","Electric","Ongole",2600,4500,"available","https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=900&q=80","Quiet electric vehicle for efficient urban travel."),
            ("AP-07-MN-7070","Toyota","Fortuner","SUV",2023,7,"Automatic","Diesel","Vijayawada",5200,8000,"available","https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=900&q=80","Premium seven-seat SUV for long-distance journeys."),
            ("AP-08-OP-8080","Royal Enfield","Classic 350","Bike",2024,2,"Manual","Petrol","Guntur",900,1500,"available","https://images.unsplash.com/photo-1558981806-ec527fa84c39?auto=format&fit=crop&w=900&q=80","Classic motorcycle for flexible city and weekend trips."),
            ("AP-09-QR-9090","Mahindra","XUV700","SUV",2024,7,"Automatic","Diesel","Ongole",3500,5500,"maintenance","https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=900&q=80","Premium family SUV currently undergoing scheduled maintenance."),
            ("AP-10-ST-1111","Hyundai","i20","Hatchback",2024,5,"Manual","Petrol","Vijayawada",1700,2800,"available","https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=900&q=80","Compact hatchback with comfortable city driving."),
        ]
        for v in vehicles:
            conn.execute("""
                INSERT OR IGNORE INTO vehicles(
                    registration_no,brand,model,category,year,seats,transmission,
                    fuel_type,location,daily_rate,deposit,status,image_url,description
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, v)

if __name__ == "__main__":
    seed("--reset" in sys.argv)
    print("Database initialized and demo data seeded.")
