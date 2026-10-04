from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin', 'operations', 'driver'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to driver profile if role is 'driver'
    driver_profile = relationship("Driver", back_populates="user", uselist=False, cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True)
    driver_id = Column(String(30), unique=True, index=True, nullable=False)  # e.g., DRV-101
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(30), default="Active")  # 'Active', 'On Duty', 'Off Duty', 'Inactive'

    user = relationship("User", back_populates="driver_profile")
    trips = relationship("Trip", back_populates="driver")
    assignments = relationship("Assignment", back_populates="driver")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "driver_id": self.driver_id,
            "name": self.name,
            "phone": self.phone,
            "license_number": self.license_number,
            "status": self.status,
            "username": self.user.username if self.user else None,
            "email": self.user.email if self.user else None
        }

class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String(30), unique=True, index=True, nullable=False)  # e.g., BUS-101
    registration_number = Column(String(30), unique=True, nullable=False)     # e.g., AP29-BD-1001
    bus_type = Column(String(50), nullable=False)                             # 'Standard AC', 'Express Non-AC', 'Electric City', 'Volvo Luxury'
    capacity = Column(Integer, default=45)
    status = Column(String(30), default="Available")                          # 'Available', 'Assigned', 'On Route', 'Out of Service'
    maintenance_status = Column(String(30), default="Good")                   # 'Good', 'Due for Service', 'Under Maintenance'

    trips = relationship("Trip", back_populates="bus")
    assignments = relationship("Assignment", back_populates="bus")

    def to_dict(self):
        return {
            "id": self.id,
            "bus_number": self.bus_number,
            "registration_number": self.registration_number,
            "bus_type": self.bus_type,
            "capacity": self.capacity,
            "status": self.status,
            "maintenance_status": self.maintenance_status
        }

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    route_number = Column(String(30), unique=True, index=True, nullable=False) # e.g., RT-204
    source = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    stops = Column(Text, nullable=True)                                         # Comma separated
    status = Column(String(30), default="Active")                              # 'Active', 'Inactive', 'Under Construction'

    trips = relationship("Trip", back_populates="route")

    def to_dict(self):
        return {
            "id": self.id,
            "route_number": self.route_number,
            "source": self.source,
            "destination": self.destination,
            "stops": self.stops,
            "status": self.status
        }

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    departure_time = Column(String(50), nullable=False)  # ISO or formatted time
    arrival_time = Column(String(50), nullable=False)
    status = Column(String(30), default="Scheduled")     # 'Scheduled', 'Assigned', 'In Progress', 'Completed', 'Cancelled'

    route = relationship("Route", back_populates="trips")
    bus = relationship("Bus", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")
    assignments = relationship("Assignment", back_populates="trip", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "route_id": self.route_id,
            "route_number": self.route.route_number if self.route else None,
            "source": self.route.source if self.route else None,
            "destination": self.route.destination if self.route else None,
            "bus_id": self.bus_id,
            "bus_number": self.bus.bus_number if self.bus else "Unassigned",
            "driver_id": self.driver_id,
            "driver_name": self.driver.name if self.driver else "Unassigned",
            "driver_code": self.driver.driver_id if self.driver else None,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "status": self.status
        }

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String(255), nullable=True)
    status = Column(String(30), default="Active") # 'Active', 'Completed', 'Replaced'

    trip = relationship("Trip", back_populates="assignments")
    bus = relationship("Bus", back_populates="assignments")
    driver = relationship("Driver", back_populates="assignments")

    def to_dict(self):
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "bus_id": self.bus_id,
            "bus_number": self.bus.bus_number if self.bus else None,
            "driver_id": self.driver_id,
            "driver_name": self.driver.name if self.driver else None,
            "assigned_date": self.assigned_date.strftime("%Y-%m-%d %H:%M:%S") if self.assigned_date else None,
            "notes": self.notes,
            "status": self.status
        }

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(50), nullable=True)
    role = Column(String(20), nullable=True)
    action = Column(String(50), nullable=False) # e.g. "Login", "User created", "Bus assigned"
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username or (self.user.username if self.user else "System"),
            "role": self.role or (self.user.role if self.user else "System"),
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None
        }
