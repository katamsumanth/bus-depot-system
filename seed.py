import os
from datetime import datetime, timedelta
from database import SessionLocal, init_db, engine
import models
from auth import hash_password

def seed_database():
    print("Initializing database tables...")
    init_db()

    db = SessionLocal()
    try:
        # Check if already seeded
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if admin_user:
            print("Database already contains seed data. Cleaning and re-seeding for clean state...")
            models.Base.metadata.drop_all(bind=engine)
            models.Base.metadata.create_all(bind=engine)

        print("Seeding Users...")
        # 1. Admin Account
        admin = models.User(
            username="admin",
            email="admin@depot.com",
            password_hash=hash_password("Admin@123"),
            role="admin",
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=30)
        )
        # 2. Operations Staff Account
        operations = models.User(
            username="operations",
            email="ops@depot.com",
            password_hash=hash_password("Ops@123"),
            role="operations",
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=20)
        )
        # 3. Driver 1 Account
        driver1_user = models.User(
            username="driver1",
            email="driver1@depot.com",
            password_hash=hash_password("Driver@123"),
            role="driver",
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=15)
        )
        # 4. Driver 2 Account
        driver2_user = models.User(
            username="driver2",
            email="driver2@depot.com",
            password_hash=hash_password("Driver@123"),
            role="driver",
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=10)
        )

        db.add_all([admin, operations, driver1_user, driver2_user])
        db.commit()

        print("Seeding Drivers...")
        # Link driver profiles
        drv1 = models.Driver(
            user_id=driver1_user.id,
            driver_id="DRV-101",
            name="Rajesh Kumar",
            phone="+91 98765 43210",
            license_number="DL-AP29-2018-0091",
            status="On Duty"
        )
        drv2 = models.Driver(
            user_id=driver2_user.id,
            driver_id="DRV-102",
            name="Suresh Reddy",
            phone="+91 98765 43211",
            license_number="DL-AP29-2019-0145",
            status="Active"
        )
        drv3 = models.Driver(
            user_id=None,
            driver_id="DRV-103",
            name="Anil Sharma",
            phone="+91 98765 43212",
            license_number="DL-AP29-2020-0321",
            status="Active"
        )
        drv4 = models.Driver(
            user_id=None,
            driver_id="DRV-104",
            name="Vikram Singh",
            phone="+91 98765 43213",
            license_number="DL-AP29-2017-0882",
            status="Off Duty"
        )
        db.add_all([drv1, drv2, drv3, drv4])
        db.commit()

        print("Seeding Buses...")
        buses = [
            models.Bus(
                bus_number="BUS-101",
                registration_number="AP29-BD-1001",
                bus_type="Volvo Luxury",
                capacity=48,
                status="Assigned",
                maintenance_status="Good"
            ),
            models.Bus(
                bus_number="BUS-102",
                registration_number="AP29-BD-1002",
                bus_type="Electric City",
                capacity=40,
                status="Available",
                maintenance_status="Good"
            ),
            models.Bus(
                bus_number="BUS-103",
                registration_number="AP29-BD-1003",
                bus_type="Standard AC",
                capacity=52,
                status="Available",
                maintenance_status="Good"
            ),
            models.Bus(
                bus_number="BUS-104",
                registration_number="AP29-BD-1004",
                bus_type="Express Non-AC",
                capacity=55,
                status="Out of Service",
                maintenance_status="Under Maintenance"
            ),
            models.Bus(
                bus_number="BUS-105",
                registration_number="AP29-BD-1005",
                bus_type="Electric City",
                capacity=40,
                status="Available",
                maintenance_status="Due for Service"
            ),
            models.Bus(
                bus_number="BUS-106",
                registration_number="AP29-BD-1006",
                bus_type="Standard AC",
                capacity=50,
                status="Available",
                maintenance_status="Good"
            )
        ]
        db.add_all(buses)
        db.commit()

        print("Seeding Routes...")
        routes = [
            models.Route(
                route_number="RT-101",
                source="Depot Central Terminal",
                destination="Cyber Gateway Tech Park",
                stops="Depot Central, Ring Road Jn, Outer Bypass, InfoCity Gate, Cyber Gateway",
                status="Active"
            ),
            models.Route(
                route_number="RT-102",
                source="Depot Central Terminal",
                destination="International Airport T2",
                stops="Depot Central, South Expressway, Aero Plaza, Cargo Complex, Airport T2",
                status="Active"
            ),
            models.Route(
                route_number="RT-103",
                source="East Suburb Terminal",
                destination="Metro Central Hub",
                stops="East Suburb, Market Cross, University Circle, North Gate, Metro Central",
                status="Active"
            ),
            models.Route(
                route_number="RT-104",
                source="South Campus Terminal",
                destination="Downtown Business District",
                stops="South Campus, Hillside Ave, City Center, Financial Towers, Downtown",
                status="Active"
            )
        ]
        db.add_all(routes)
        db.commit()

        print("Seeding Trips & Assignments...")
        trip1 = models.Trip(
            route_id=routes[0].id,
            bus_id=buses[0].id,
            driver_id=drv1.id,
            departure_time="08:30 AM",
            arrival_time="10:00 AM",
            status="In Progress"
        )
        trip2 = models.Trip(
            route_id=routes[1].id,
            bus_id=buses[1].id,
            driver_id=drv2.id,
            departure_time="11:00 AM",
            arrival_time="12:45 PM",
            status="Scheduled"
        )
        trip3 = models.Trip(
            route_id=routes[2].id,
            bus_id=None,
            driver_id=None,
            departure_time="02:00 PM",
            arrival_time="03:30 PM",
            status="Scheduled"
        )
        trip4 = models.Trip(
            route_id=routes[3].id,
            bus_id=buses[2].id,
            driver_id=drv1.id,
            departure_time="06:00 AM",
            arrival_time="07:30 AM",
            status="Completed"
        )
        db.add_all([trip1, trip2, trip3, trip4])
        db.commit()

        # Create Assignment record
        assign1 = models.Assignment(
            trip_id=trip1.id,
            bus_id=buses[0].id,
            driver_id=drv1.id,
            assigned_by=operations.id,
            assigned_date=datetime.utcnow() - timedelta(hours=2),
            notes="Morning Peak Hour Commute Route RT-101",
            status="Active"
        )
        db.add(assign1)

        print("Seeding Activity Logs...")
        logs = [
            models.ActivityLog(
                user_id=admin.id,
                username="admin",
                role="admin",
                action="System Initialized",
                details="Initial database schema and baseline data configured",
                timestamp=datetime.utcnow() - timedelta(days=1)
            ),
            models.ActivityLog(
                user_id=operations.id,
                username="operations",
                role="operations",
                action="Trip Created",
                details="Operations created Trip #1 for route RT-101 (Bus: BUS-101, Driver: DRV-101)",
                timestamp=datetime.utcnow() - timedelta(hours=3)
            ),
            models.ActivityLog(
                user_id=driver1_user.id,
                username="driver1",
                role="driver",
                action="Trip Status Updated by Driver",
                details="Driver Rajesh Kumar started Trip #1 (Status: In Progress)",
                timestamp=datetime.utcnow() - timedelta(hours=1)
            )
        ]
        db.add_all(logs)
        db.commit()

        print("\n=======================================================")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=======================================================")
        print("Default Demo Accounts Created:")
        print("  1. Admin:")
        print("     Username: admin")
        print("     Password: Admin@123")
        print("     Role:     admin")
        print("  2. Operations Staff:")
        print("     Username: operations")
        print("     Password: Ops@123")
        print("     Role:     operations")
        print("  3. Driver 1 (Rajesh Kumar):")
        print("     Username: driver1")
        print("     Password: Driver@123")
        print("     Role:     driver")
        print("  4. Driver 2 (Suresh Reddy):")
        print("     Username: driver2")
        print("     Password: Driver@123")
        print("     Role:     driver")
        print("=======================================================\n")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
