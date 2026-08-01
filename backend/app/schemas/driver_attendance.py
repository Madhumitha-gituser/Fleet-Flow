from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.driver_attendance import AttendanceStatus


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class DriverAttendanceCreate(BaseModel):
    driver_id: int
    date: date
    attendance_status: AttendanceStatus
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None


class DriverAttendanceUpdate(BaseModel):
    attendance_status: AttendanceStatus
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class DriverAttendanceResponse(BaseModel):
    id: int
    driver_id: int
    date: date
    attendance_status: AttendanceStatus
    check_in_time: Optional[datetime]
    check_out_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
