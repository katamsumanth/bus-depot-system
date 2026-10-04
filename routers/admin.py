from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
import models
import schemas
from auth import require_role, hash_password, log_activity

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_role(["admin"]))])

# ==========================================
# 1. ADMIN DASHBOARD STATS
# ==========================================
@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    total_buses = db.query(models.Bus).count()
    available_buses = db.query(models.Bus).filter(models.Bus.status == "Available").count()
    maintenance_buses = db.query(models.Bus).filter(
        (models.Bus.maintenance_status == "Under Maintenance") | (models.Bus.maintenance_status == "Due for Service")
    ).count()

    total_drivers = db.query(models.Driver).count()
    active_drivers = db.query(models.Driver).filter(models.Driver.status == "Active").count()
    on_duty_drivers = db.query(models.Driver).filter(models.Driver.status == "On Duty").count()

    total_routes = db.query(models.Route).count()
    total_trips = db.query(models.Trip).count()
    scheduled_trips = db.query(models.Trip).filter(models.Trip.status == "Scheduled").count()
    active_trips = db.query(models.Trip).filter(models.Trip.status == "In Progress").count()
    completed_trips = db.query(models.Trip).filter(models.Trip.status == "Completed").count()

    total_users = db.query(models.User).count()
    active_users = db.query(models.User).filter(models.User.is_active == True).count()

    return {
        "buses": {
            "total": total_buses,
            "available": available_buses,
            "maintenance": maintenance_buses,
            "assigned": total_buses - available_buses - maintenance_buses if (total_buses - available_buses - maintenance_buses) >= 0 else 0
        },
        "drivers": {
            "total": total_drivers,
            "active": active_drivers,
            "on_duty": on_duty_drivers,
            "off_duty": total_drivers - active_drivers - on_duty_drivers
        },
        "routes": {
            "total": total_routes
        },
        "trips": {
            "total": total_trips,
            "scheduled": scheduled_trips,
            "active": active_trips,
            "completed": completed_trips
        },
        "users": {
            "total": total_users,
            "active": active_users
        }
    }

# ==========================================
# 2. USER MANAGEMENT
# ==========================================
@router.get("/users")
def get_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)
    if search:
        s = f"%{search}%"
        query = query.filter((models.User.username.ilike(s)) | (models.User.email.ilike(s)))
    users = query.order_by(models.User.id.desc()).all()
    return [u.to_dict() for u in users]

@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    # Check existing username or email
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already exists.")
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    if user_in.role not in ["admin", "operations", "driver"]:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    new_user = models.User(
        username=user_in.username.strip(),
        email=user_in.email.strip(),
        password_hash=hash_password(user_in.password),
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "User Created", f"Admin created user {new_user.username} with role {new_user.role}")

    return new_user.to_dict()

@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user_update.email:
        existing = db.query(models.User).filter(models.User.email == user_update.email, models.User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email is already used by another user.")
        user.email = user_update.email

    if user_update.role:
        if user_update.role not in ["admin", "operations", "driver"]:
            raise HTTPException(status_code=400, detail="Invalid role.")
        user.role = user_update.role

    if user_update.is_active is not None:
        # Prevent deactivating own account
        if user.id == current_user.id and not user_update.is_active:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account.")
        user.is_active = user_update.is_active

    if user_update.password and user_update.password.strip():
        user.password_hash = hash_password(user_update.password.strip())

    db.commit()
    db.refresh(user)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "User Updated", f"Admin updated user {user.username}")

    return user.to_dict()

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account.")

    username = user.username
    db.delete(user)
    db.commit()

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "User Deleted", f"Admin deleted user {username}")

    return {"message": f"User {username} successfully deleted."}

# ==========================================
# 3. BUS MANAGEMENT
# ==========================================
@router.get("/buses")
def get_buses(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Bus)
    if status:
        query = query.filter(models.Bus.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter((models.Bus.bus_number.ilike(s)) | (models.Bus.registration_number.ilike(s)) | (models.Bus.bus_type.ilike(s)))
    buses = query.order_by(models.Bus.id.desc()).all()
    return [b.to_dict() for b in buses]

@router.post("/buses", status_code=status.HTTP_201_CREATED)
def create_bus(
    bus_in: schemas.BusCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    if db.query(models.Bus).filter(models.Bus.bus_number == bus_in.bus_number).first():
        raise HTTPException(status_code=400, detail="Bus Number already exists.")
    if db.query(models.Bus).filter(models.Bus.registration_number == bus_in.registration_number).first():
        raise HTTPException(status_code=400, detail="Registration Number already registered.")

    new_bus = models.Bus(
        bus_number=bus_in.bus_number.strip().upper(),
        registration_number=bus_in.registration_number.strip().upper(),
        bus_type=bus_in.bus_type,
        capacity=bus_in.capacity,
        status=bus_in.status,
        maintenance_status=bus_in.maintenance_status
    )
    db.add(new_bus)
    db.commit()
    db.refresh(new_bus)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Bus Created", f"Admin added bus {new_bus.bus_number}")

    return new_bus.to_dict()

@router.put("/buses/{bus_id}")
def update_bus(
    bus_id: int,
    bus_update: schemas.BusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    bus = db.query(models.Bus).filter(models.Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found.")

    if bus_update.bus_number:
        existing = db.query(models.Bus).filter(models.Bus.bus_number == bus_update.bus_number, models.Bus.id != bus_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bus number already in use.")
        bus.bus_number = bus_update.bus_number.strip().upper()

    if bus_update.registration_number:
        existing = db.query(models.Bus).filter(models.Bus.registration_number == bus_update.registration_number, models.Bus.id != bus_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Registration number already in use.")
        bus.registration_number = bus_update.registration_number.strip().upper()

    if bus_update.bus_type:
        bus.bus_type = bus_update.bus_type
    if bus_update.capacity is not None:
        bus.capacity = bus_update.capacity
    if bus_update.status:
        bus.status = bus_update.status
    if bus_update.maintenance_status:
        bus.maintenance_status = bus_update.maintenance_status

    db.commit()
    db.refresh(bus)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Bus Updated", f"Admin updated bus {bus.bus_number}")

    return bus.to_dict()

@router.delete("/buses/{bus_id}")
def delete_bus(
    bus_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    bus = db.query(models.Bus).filter(models.Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found.")

    # Check if assigned to any active trip
    active_trip = db.query(models.Trip).filter(models.Trip.bus_id == bus_id, models.Trip.status.in_(["Scheduled", "In Progress", "Assigned"])).first()
    if active_trip:
        raise HTTPException(status_code=400, detail="Cannot delete bus with active or scheduled trips. Reassign trips first.")

    bus_num = bus.bus_number
    db.delete(bus)
    db.commit()

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Bus Deleted", f"Admin deleted bus {bus_num}")

    return {"message": f"Bus {bus_num} deleted successfully."}

# ==========================================
# 4. DRIVER MANAGEMENT
# ==========================================
@router.get("/drivers")
def get_drivers(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Driver)
    if status:
        query = query.filter(models.Driver.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter((models.Driver.name.ilike(s)) | (models.Driver.driver_id.ilike(s)) | (models.Driver.license_number.ilike(s)))
    drivers = query.order_by(models.Driver.id.desc()).all()
    return [d.to_dict() for d in drivers]

@router.post("/drivers", status_code=status.HTTP_201_CREATED)
def create_driver(
    driver_in: schemas.DriverCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    if db.query(models.Driver).filter(models.Driver.driver_id == driver_in.driver_id).first():
        raise HTTPException(status_code=400, detail="Driver ID already exists.")
    if db.query(models.Driver).filter(models.Driver.license_number == driver_in.license_number).first():
        raise HTTPException(status_code=400, detail="License Number already registered.")

    user_id = driver_in.user_id

    # If login credentials provided, create user account automatically
    if driver_in.username and driver_in.password and driver_in.email:
        if db.query(models.User).filter(models.User.username == driver_in.username).first():
            raise HTTPException(status_code=400, detail="Username for driver account already taken.")
        if db.query(models.User).filter(models.User.email == driver_in.email).first():
            raise HTTPException(status_code=400, detail="Email for driver account already taken.")

        driver_user = models.User(
            username=driver_in.username.strip(),
            email=driver_in.email.strip(),
            password_hash=hash_password(driver_in.password.strip()),
            role="driver",
            is_active=True
        )
        db.add(driver_user)
        db.flush()
        user_id = driver_user.id

    new_driver = models.Driver(
        user_id=user_id,
        driver_id=driver_in.driver_id.strip().upper(),
        name=driver_in.name.strip(),
        phone=driver_in.phone.strip(),
        license_number=driver_in.license_number.strip().upper(),
        status=driver_in.status
    )
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Driver Created", f"Admin created driver {new_driver.name} ({new_driver.driver_id})")

    return new_driver.to_dict()

@router.put("/drivers/{driver_id}")
def update_driver(
    driver_id: int,
    driver_update: schemas.DriverUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found.")

    if driver_update.license_number:
        existing = db.query(models.Driver).filter(models.Driver.license_number == driver_update.license_number, models.Driver.id != driver_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="License number already in use.")
        driver.license_number = driver_update.license_number.strip().upper()

    if driver_update.name:
        driver.name = driver_update.name.strip()
    if driver_update.phone:
        driver.phone = driver_update.phone.strip()
    if driver_update.status:
        driver.status = driver_update.status

    db.commit()
    db.refresh(driver)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Driver Updated", f"Admin updated driver {driver.name} ({driver.driver_id})")

    return driver.to_dict()

@router.delete("/drivers/{driver_id}")
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found.")

    # Check if driver has active trips
    active_trip = db.query(models.Trip).filter(models.Trip.driver_id == driver_id, models.Trip.status.in_(["Scheduled", "In Progress", "Assigned"])).first()
    if active_trip:
        raise HTTPException(status_code=400, detail="Cannot delete driver assigned to scheduled or active trips.")

    driver_name = driver.name
    # Also delete associated user account if one exists
    if driver.user:
        db.delete(driver.user)
    db.delete(driver)
    db.commit()

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Driver Deleted", f"Admin deleted driver {driver_name}")

    return {"message": f"Driver {driver_name} deleted successfully."}

# ==========================================
# 5. ROUTE MANAGEMENT
# ==========================================
@router.get("/routes")
def get_routes(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Route)
    if status:
        query = query.filter(models.Route.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter((models.Route.route_number.ilike(s)) | (models.Route.source.ilike(s)) | (models.Route.destination.ilike(s)))
    routes = query.order_by(models.Route.id.desc()).all()
    return [r.to_dict() for r in routes]

@router.post("/routes", status_code=status.HTTP_201_CREATED)
def create_route(
    route_in: schemas.RouteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    if db.query(models.Route).filter(models.Route.route_number == route_in.route_number).first():
        raise HTTPException(status_code=400, detail="Route number already exists.")

    new_route = models.Route(
        route_number=route_in.route_number.strip().upper(),
        source=route_in.source.strip(),
        destination=route_in.destination.strip(),
        stops=route_in.stops.strip() if route_in.stops else None,
        status=route_in.status
    )
    db.add(new_route)
    db.commit()
    db.refresh(new_route)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Route Created", f"Admin created route {new_route.route_number}")

    return new_route.to_dict()

@router.put("/routes/{route_id}")
def update_route(
    route_id: int,
    route_update: schemas.RouteUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    if route_update.route_number:
        existing = db.query(models.Route).filter(models.Route.route_number == route_update.route_number, models.Route.id != route_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Route number already exists.")
        route.route_number = route_update.route_number.strip().upper()

    if route_update.source:
        route.source = route_update.source.strip()
    if route_update.destination:
        route.destination = route_update.destination.strip()
    if route_update.stops is not None:
        route.stops = route_update.stops.strip()
    if route_update.status:
        route.status = route_update.status

    db.commit()
    db.refresh(route)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Route Updated", f"Admin updated route {route.route_number}")

    return route.to_dict()

@router.delete("/routes/{route_id}")
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    active_trips = db.query(models.Trip).filter(models.Trip.route_id == route_id).count()
    if active_trips > 0:
        raise HTTPException(status_code=400, detail="Cannot delete route associated with existing trips.")

    route_num = route.route_number
    db.delete(route)
    db.commit()

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Route Deleted", f"Admin deleted route {route_num}")

    return {"message": f"Route {route_num} deleted successfully."}

# ==========================================
# 6. TRIP MANAGEMENT (ADMIN)
# ==========================================
@router.get("/trips")
def get_trips(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Trip)
    if status:
        query = query.filter(models.Trip.status == status)
    trips = query.order_by(models.Trip.id.desc()).all()
    return [t.to_dict() for t in trips]

@router.post("/trips", status_code=status.HTTP_201_CREATED)
def create_trip(
    trip_in: schemas.TripCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    route = db.query(models.Route).filter(models.Route.id == trip_in.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")

    new_trip = models.Trip(
        route_id=trip_in.route_id,
        bus_id=trip_in.bus_id,
        driver_id=trip_in.driver_id,
        departure_time=trip_in.departure_time,
        arrival_time=trip_in.arrival_time,
        status=trip_in.status
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    # If bus and driver assigned, create assignment record and update statuses
    if trip_in.bus_id and trip_in.driver_id:
        assignment = models.Assignment(
            trip_id=new_trip.id,
            bus_id=trip_in.bus_id,
            driver_id=trip_in.driver_id,
            assigned_by=current_user.id,
            status="Active"
        )
        db.add(assignment)
        bus = db.query(models.Bus).filter(models.Bus.id == trip_in.bus_id).first()
        driver = db.query(models.Driver).filter(models.Driver.id == trip_in.driver_id).first()
        if bus:
            bus.status = "Assigned"
        if driver:
            driver.status = "On Duty"
        db.commit()

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Trip Created", f"Admin created trip #{new_trip.id} for route {route.route_number}")

    return new_trip.to_dict()

@router.put("/trips/{trip_id}")
def update_trip(
    trip_id: int,
    trip_update: schemas.TripUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")

    if trip_update.route_id is not None:
        trip.route_id = trip_update.route_id
    if trip_update.bus_id is not None:
        trip.bus_id = trip_update.bus_id
    if trip_update.driver_id is not None:
        trip.driver_id = trip_update.driver_id
    if trip_update.departure_time:
        trip.departure_time = trip_update.departure_time
    if trip_update.arrival_time:
        trip.arrival_time = trip_update.arrival_time
    if trip_update.status:
        trip.status = trip_update.status
        if trip.status in ["Completed", "Cancelled"]:
            # Release bus and driver
            if trip.bus:
                trip.bus.status = "Available"
            if trip.driver:
                trip.driver.status = "Active"

    db.commit()
    db.refresh(trip)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Trip Updated", f"Admin updated trip #{trip.id}")

    return trip.to_dict()

@router.delete("/trips/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")

    # If bus and driver were assigned, release them
    if trip.bus and trip.bus.status == "Assigned":
        trip.bus.status = "Available"
    if trip.driver and trip.driver.status == "On Duty":
        trip.driver.status = "Active"

    db.delete(trip)
    db.commit()

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Trip Deleted", f"Admin deleted trip #{trip_id}")

    return {"message": f"Trip #{trip_id} deleted successfully."}

# ==========================================
# 7. REPORTS & ACTIVITY LOGS
# ==========================================
@router.get("/reports")
def get_admin_reports(db: Session = Depends(get_db)):
    # Bus by status
    bus_status_counts = dict(db.query(models.Bus.status, func.count(models.Bus.id)).group_by(models.Bus.status).all())
    # Bus by maintenance status
    bus_maint_counts = dict(db.query(models.Bus.maintenance_status, func.count(models.Bus.id)).group_by(models.Bus.maintenance_status).all())
    # Driver status
    driver_status_counts = dict(db.query(models.Driver.status, func.count(models.Driver.id)).group_by(models.Driver.status).all())
    # Trip status
    trip_status_counts = dict(db.query(models.Trip.status, func.count(models.Trip.id)).group_by(models.Trip.status).all())

    # Routes summary
    routes = db.query(models.Route).all()
    route_data = []
    for r in routes:
        t_count = len(r.trips)
        route_data.append({
            "route_number": r.route_number,
            "source": r.source,
            "destination": r.destination,
            "total_trips": t_count,
            "status": r.status
        })

    return {
        "bus_status": bus_status_counts,
        "bus_maintenance": bus_maint_counts,
        "driver_status": driver_status_counts,
        "trip_status": trip_status_counts,
        "routes": route_data
    }

@router.get("/activity-logs")
def get_activity_logs(
    limit: int = 50,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.ActivityLog)
    if action:
        query = query.filter(models.ActivityLog.action.ilike(f"%{action}%"))
    logs = query.order_by(models.ActivityLog.id.desc()).limit(limit).all()
    return [l.to_dict() for l in logs]
