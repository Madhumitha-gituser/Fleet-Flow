from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.driver_assignment import AssignmentStatus


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class DriverAssignmentCreate(BaseModel):
    driver_id: int
    vehicle_id: int
    trip_id: Optional[int] = None
    assignment_date: date
    assignment_status: AssignmentStatus = AssignmentStatus.ACTIVE
    remarks: Optional[str] = None


class DriverAssignmentUpdate(BaseModel):
    driver_id: int
    vehicle_id: int
    trip_id: Optional[int] = None
    assignment_date: date
    assignment_status: AssignmentStatus
    remarks: Optional[str] = None


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class DriverAssignmentResponse(BaseModel):
    id: int
    driver_id: int
    vehicle_id: int
    trip_id: Optional[int]
    assignment_date: date
    assignment_status: AssignmentStatus
    remarks: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
