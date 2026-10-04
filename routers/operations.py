from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
import models
import schemas
from auth import require_role, log_activity

router = APIRouter(prefix="/operations", tags=["Operations"], dependencies=[Depends(require_role(["operations", "admin"]))])

# ==========================================
# 1. OPERATIONS DASHBOARD STATS
# ==========================================
@router.get("/stats")
def get_operations_stats(db: Session = Depends(get_db)):
    available_buses = db.query(models.Bus).filter(models.Bus.status == "Available").count()
    assigned_buses = db.query(models.Bus).filter(models.Bus.status == "Assigned").count()
    maintenance_buses = db.query(models.Bus).filter(
        models.Bus.maintenance_status.in_(["Under Maintenance", "Due for Service"])
    ).count()

    available_drivers = db.query(models.Driver).filter(models.Driver.status == "Active").count()
    on_duty_drivers = db.query(models.Driver).filter(models.Driver.status == "On Duty").count()

    today_trips = db.query(models.Trip).count()
    active_trips = db.query(models.Trip).filter(models.Trip.status == "In Progress").count()
    scheduled_trips = db.query(models.Trip).filter(models.Trip.status == "Scheduled").count()
    pending_assignments = db.query(models.Trip).filter(
        (models.Trip.bus_id == None) | (models.Trip.driver_id == None)
    ).count()

    return {
        "available_buses": available_buses,
        "assigned_buses": assigned_buses,
        "maintenance_buses": maintenance_buses,
        "available_drivers": available_drivers,
        "on_duty_drivers": on_duty_drivers,
        "today_trips": today_trips,
        "active_trips": active_trips,
        "scheduled_trips": scheduled_trips,
        "pending_assignments": pending_assignments
    }

# ==========================================
# 2. BUS OPERATIONS
# ==========================================
@router.get("/buses")
def get_operational_buses(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Bus)
    if status:
        query = query.filter(models.Bus.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter((models.Bus.bus_number.ilike(s)) | (models.Bus.registration_number.ilike(s)))
    buses = query.order_by(models.Bus.bus_number.asc()).all()
    return [b.to_dict() for b in buses]

@router.put("/buses/{bus_id}/status")
def update_bus_status(
    bus_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["operations", "admin"]))
):
    bus = db.query(models.Bus).filter(models.Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found.")

    new_status = status_update.get("status")
    if new_status:
        bus.status = new_status
    new_maint = status_update.get("maintenance_status")
    if new_maint:
        bus.maintenance_status = new_maint

    db.commit()
    db.refresh(bus)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Bus Status Updated", f"Operations updated bus {bus.bus_number} to {bus.status} ({bus.maintenance_status})")

    return bus.to_dict()

# ==========================================
# 3. DRIVER OPERATIONS
# ==========================================
@router.get("/drivers")
def get_operational_drivers(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Driver)
    if status:
        query = query.filter(models.Driver.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter((models.Driver.name.ilike(s)) | (models.Driver.driver_id.ilike(s)))
    drivers = query.order_by(models.Driver.driver_id.asc()).all()
    return [d.to_dict() for d in drivers]

@router.put("/drivers/{driver_id}/status")
def update_driver_status(
    driver_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["operations", "admin"]))
):
    driver = db.query(models.Driver).filter(models.Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found.")

    new_status = status_update.get("status")
    if new_status:
        driver.status = new_status

    db.commit()
    db.refresh(driver)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Driver Status Updated", f"Operations updated driver {driver.name} to {driver.status}")

    return driver.to_dict()

# ==========================================
# 4. ROUTE OPERATIONS
# ==========================================
@router.get("/routes")
def get_operational_routes(db: Session = Depends(get_db)):
    routes = db.query(models.Route).filter(models.Route.status == "Active").order_by(models.Route.route_number.asc()).all()
    return [r.to_dict() for r in routes]

# ==========================================
# 5. TRIP MANAGEMENT & ASSIGNMENTS
# ==========================================
@router.get("/trips")
def get_operational_trips(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Trip)
    if status:
        query = query.filter(models.Trip.status == status)
    trips = query.order_by(models.Trip.id.desc()).all()
    return [t.to_dict() for t in trips]

@router.post("/trips", status_code=status.HTTP_201_CREATED)
def create_operational_trip(
    trip_in: schemas.TripCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["operations", "admin"]))
):
    route = db.query(models.Route).filter(models.Route.id == trip_in.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Selected Route not found.")

    # Check bus if provided
    bus = None
    if trip_in.bus_id:
        bus = db.query(models.Bus).filter(models.Bus.id == trip_in.bus_id).first()
        if not bus:
            raise HTTPException(status_code=404, detail="Selected Bus not found.")
        if bus.status != "Available":
            raise HTTPException(status_code=400, detail=f"Bus {bus.bus_number} is currently {bus.status}.")
        if bus.maintenance_status in ["Under Maintenance"]:
            raise HTTPException(status_code=400, detail=f"Bus {bus.bus_number} is currently Under Maintenance.")

    # Check driver if provided
    driver = None
    if trip_in.driver_id:
        driver = db.query(models.Driver).filter(models.Driver.id == trip_in.driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Selected Driver not found.")
        if driver.status not in ["Active", "Off Duty"]:
            raise HTTPException(status_code=400, detail=f"Driver {driver.name} is currently {driver.status}.")

    new_trip = models.Trip(
        route_id=trip_in.route_id,
        bus_id=trip_in.bus_id,
        driver_id=trip_in.driver_id,
        departure_time=trip_in.departure_time,
        arrival_time=trip_in.arrival_time,
        status="Assigned" if (trip_in.bus_id and trip_in.driver_id) else trip_in.status
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    # If bus and driver assigned, create assignment record & update statuses
    if bus and driver:
        bus.status = "Assigned"
        driver.status = "On Duty"
        assignment = models.Assignment(
            trip_id=new_trip.id,
            bus_id=bus.id,
            driver_id=driver.id,
            assigned_by=current_user.id,
            status="Active",
            notes=f"Trip #{new_trip.id} ({route.route_number})"
        )
        db.add(assignment)
        db.commit()

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Trip Created", f"Operations created trip #{new_trip.id} for route {route.route_number}")

    return new_trip.to_dict()

@router.put("/trips/{trip_id}")
def update_operational_trip(
    trip_id: int,
    trip_update: schemas.TripUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["operations", "admin"]))
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")

    old_bus_id = trip.bus_id
    old_driver_id = trip.driver_id

    if trip_update.route_id is not None:
        trip.route_id = trip_update.route_id

    # Handle bus reassignment
    if trip_update.bus_id is not None and trip_update.bus_id != old_bus_id:
        if old_bus_id:
            old_bus = db.query(models.Bus).filter(models.Bus.id == old_bus_id).first()
            if old_bus:
                old_bus.status = "Available"
        new_bus = db.query(models.Bus).filter(models.Bus.id == trip_update.bus_id).first()
        if new_bus:
            new_bus.status = "Assigned"
        trip.bus_id = trip_update.bus_id

    # Handle driver reassignment
    if trip_update.driver_id is not None and trip_update.driver_id != old_driver_id:
        if old_driver_id:
            old_drv = db.query(models.Driver).filter(models.Driver.id == old_driver_id).first()
            if old_drv:
                old_drv.status = "Active"
        new_drv = db.query(models.Driver).filter(models.Driver.id == trip_update.driver_id).first()
        if new_drv:
            new_drv.status = "On Duty"
        trip.driver_id = trip_update.driver_id

    if trip_update.departure_time:
        trip.departure_time = trip_update.departure_time
    if trip_update.arrival_time:
        trip.arrival_time = trip_update.arrival_time

    if trip_update.status:
        trip.status = trip_update.status
        if trip.status in ["Completed", "Cancelled"]:
            if trip.bus:
                trip.bus.status = "Available"
            if trip.driver:
                trip.driver.status = "Active"

    db.commit()
    db.refresh(trip)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Trip Updated", f"Operations updated trip #{trip.id}")

    return trip.to_dict()

@router.put("/trips/{trip_id}/status")
def update_trip_status_only(
    trip_id: int,
    status_update: schemas.TripStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["operations", "admin"]))
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")

    trip.status = status_update.status
    if trip.status in ["Completed", "Cancelled"]:
        if trip.bus:
            trip.bus.status = "Available"
        if trip.driver:
            trip.driver.status = "Active"

    db.commit()
    db.refresh(trip)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Trip Status Changed", f"Operations set trip #{trip.id} status to {trip.status}")

    return trip.to_dict()

# ==========================================
# 6. ASSIGNMENTS
# ==========================================
@router.get("/assignments")
def get_assignments(db: Session = Depends(get_db)):
    assignments = db.query(models.Assignment).order_by(models.Assignment.id.desc()).all()
    return [a.to_dict() for a in assignments]

@router.post("/assignments", status_code=status.HTTP_201_CREATED)
def create_direct_assignment(
    assign_in: schemas.AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["operations", "admin"]))
):
    bus = db.query(models.Bus).filter(models.Bus.id == assign_in.bus_id).first()
    driver = db.query(models.Driver).filter(models.Driver.id == assign_in.driver_id).first()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found.")
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found.")

    bus.status = "Assigned"
    driver.status = "On Duty"

    assignment = models.Assignment(
        trip_id=assign_in.trip_id,
        bus_id=bus.id,
        driver_id=driver.id,
        assigned_by=current_user.id,
        notes=assign_in.notes or "Operational assignment",
        status="Active"
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    log_activity(db, current_user.id, current_user.username, current_user.role,
                 "Assignment Created", f"Assigned bus {bus.bus_number} to driver {driver.name}")

    return assignment.to_dict()

# ==========================================
# 7. REPORTS
# ==========================================
@router.get("/reports")
def get_operations_reports(db: Session = Depends(get_db)):
    bus_status = dict(db.query(models.Bus.status, func.count(models.Bus.id)).group_by(models.Bus.status).all())
    driver_status = dict(db.query(models.Driver.status, func.count(models.Driver.id)).group_by(models.Driver.status).all())
    trip_status = dict(db.query(models.Trip.status, func.count(models.Trip.id)).group_by(models.Trip.status).all())

    return {
        "bus_status": bus_status,
        "driver_status": driver_status,
        "trip_status": trip_status
    }
