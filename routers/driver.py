from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
from auth import require_role, log_activity

router = APIRouter(prefix="/driver", tags=["Driver"], dependencies=[Depends(require_role(["driver", "admin"]))])

def get_current_driver(current_user: models.User = Depends(require_role(["driver", "admin"])), db: Session = Depends(get_db)):
    if current_user.role == "admin":
        # If admin visits driver endpoint, return first driver for testing/demonstration
        driver = db.query(models.Driver).first()
        if not driver:
            raise HTTPException(status_code=404, detail="No driver record exists in system.")
        return driver

    driver = db.query(models.Driver).filter(models.Driver.user_id == current_user.id).first()
    if not driver:
        # Fallback by matching email or username if user_id wasn't directly linked
        driver = db.query(models.Driver).filter(
            (models.Driver.driver_id == current_user.username) |
            (models.Driver.name.ilike(f"%{current_user.username}%"))
        ).first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not linked to this user account. Please contact operations."
        )
    return driver

@router.get("/profile")
def get_driver_profile(
    driver: models.Driver = Depends(get_current_driver),
    current_user: models.User = Depends(require_role(["driver", "admin"]))
):
    profile = driver.to_dict()
    profile["username"] = current_user.username
    profile["email"] = current_user.email
    profile["role"] = current_user.role
    return profile

@router.get("/assignment")
def get_driver_assignment(
    driver: models.Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    # Find current active/in-progress or scheduled trip
    current_trip = db.query(models.Trip).filter(
        models.Trip.driver_id == driver.id,
        models.Trip.status.in_(["In Progress", "Assigned", "Scheduled"])
    ).order_by(models.Trip.id.asc()).first()

    # Find active assignment record
    active_assignment = db.query(models.Assignment).filter(
        models.Assignment.driver_id == driver.id,
        models.Assignment.status == "Active"
    ).order_by(models.Assignment.id.desc()).first()

    assigned_bus = None
    if current_trip and current_trip.bus:
        assigned_bus = current_trip.bus.to_dict()
    elif active_assignment and active_assignment.bus:
        assigned_bus = active_assignment.bus.to_dict()

    return {
        "driver": driver.to_dict(),
        "assigned_bus": assigned_bus,
        "current_trip": current_trip.to_dict() if current_trip else None,
        "assignment_notes": active_assignment.notes if active_assignment else None
    }

@router.get("/schedule")
def get_driver_schedule(
    driver: models.Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    trips = db.query(models.Trip).filter(
        models.Trip.driver_id == driver.id
    ).order_by(models.Trip.id.desc()).all()

    return [t.to_dict() for t in trips]

@router.put("/trip/{trip_id}/status")
def update_driver_trip_status(
    trip_id: int,
    status_update: schemas.TripStatusUpdate,
    driver: models.Driver = Depends(get_current_driver),
    current_user: models.User = Depends(require_role(["driver", "admin"])),
    db: Session = Depends(get_db)
):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")

    if current_user.role != "admin" and trip.driver_id != driver.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only update status for trips assigned to you."
        )

    allowed_transitions = ["In Progress", "Completed"]
    if status_update.status not in allowed_transitions and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Drivers can only transition trips to {allowed_transitions}."
        )

    old_status = trip.status
    trip.status = status_update.status

    if trip.status == "In Progress":
        driver.status = "On Duty"
        if trip.bus:
            trip.bus.status = "On Route"

    elif trip.status == "Completed":
        driver.status = "Active"
        if trip.bus:
            trip.bus.status = "Available"

        # Update assignment status if exists
        assignment = db.query(models.Assignment).filter(
            models.Assignment.trip_id == trip.id
        ).first()
        if assignment:
            assignment.status = "Completed"

    db.commit()
    db.refresh(trip)

    log_activity(
        db,
        current_user.id,
        current_user.username,
        current_user.role,
        "Trip Status Updated by Driver",
        f"Driver {driver.name} changed Trip #{trip.id} status from '{old_status}' to '{trip.status}'"
    )

    return trip.to_dict()
