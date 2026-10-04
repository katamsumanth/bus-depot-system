from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Auth Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    redirect_url: str

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str # 'admin', 'operations', 'driver'
    is_active: bool = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# Bus Schemas
class BusBase(BaseModel):
    bus_number: str
    registration_number: str
    bus_type: str
    capacity: int = 45
    status: str = "Available"
    maintenance_status: str = "Good"

class BusCreate(BusBase):
    pass

class BusUpdate(BaseModel):
    bus_number: Optional[str] = None
    registration_number: Optional[str] = None
    bus_type: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    maintenance_status: Optional[str] = None

class BusResponse(BusBase):
    id: int

    class Config:
        from_attributes = True

# Driver Schemas
class DriverBase(BaseModel):
    driver_id: str
    name: str
    phone: str
    license_number: str
    status: str = "Active"

class DriverCreate(DriverBase):
    user_id: Optional[int] = None
    # Optionally create associated user account directly:
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    status: Optional[str] = None

class DriverResponse(DriverBase):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True

# Route Schemas
class RouteBase(BaseModel):
    route_number: str
    source: str
    destination: str
    stops: Optional[str] = None
    status: str = "Active"

class RouteCreate(RouteBase):
    pass

class RouteUpdate(BaseModel):
    route_number: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    stops: Optional[str] = None
    status: Optional[str] = None

class RouteResponse(RouteBase):
    id: int

    class Config:
        from_attributes = True

# Trip Schemas
class TripBase(BaseModel):
    route_id: int
    bus_id: Optional[int] = None
    driver_id: Optional[int] = None
    departure_time: str
    arrival_time: str
    status: str = "Scheduled"

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    route_id: Optional[int] = None
    bus_id: Optional[int] = None
    driver_id: Optional[int] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    status: Optional[str] = None

class TripStatusUpdate(BaseModel):
    status: str # 'Scheduled', 'Assigned', 'In Progress', 'Completed', 'Cancelled'

class TripResponse(TripBase):
    id: int
    route_number: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    bus_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_code: Optional[str] = None

    class Config:
        from_attributes = True

# Assignment Schemas
class AssignmentCreate(BaseModel):
    trip_id: Optional[int] = None
    bus_id: int
    driver_id: int
    notes: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: int
    trip_id: Optional[int] = None
    bus_id: int
    bus_number: Optional[str] = None
    driver_id: int
    driver_name: Optional[str] = None
    assigned_date: Optional[str] = None
    notes: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

# Activity Log Schemas
class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    action: str
    details: Optional[str] = None
    timestamp: Optional[str] = None

    class Config:
        from_attributes = True
