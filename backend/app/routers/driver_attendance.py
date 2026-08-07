from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.driver_attendance import (
    DriverAttendanceCreate,
    DriverAttendanceUpdate,
    DriverAttendanceResponse,
)
from app.services import driver_attendance_service
from app.utils.security import has_role
from app.utils.audit_log import log_action

router = APIRouter(
    prefix="/driver-attendance",
    tags=["Driver Attendance"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=DriverAttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a driver attendance record",
    description=(
        "Record attendance for a driver on a specific date.  \n\n"
        "**Validation:**\n"
        "- `driver_id` must reference an existing driver.\n"
        "- Only **one record per driver per date** is allowed — "
        "a second POST for the same driver + date returns HTTP 409."
    ),
)
def add_attendance(
    payload: DriverAttendanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = driver_attendance_service.create_attendance(payload, db)
    log_action(db, action="CREATE", resource="DriverAttendance", resource_id=res.id, details=f"Logged attendance for driver ID {res.driver_id} on {res.date} as {res.attendance_status.value if hasattr(res.attendance_status, 'value') else res.attendance_status}", user=current_user)
    return res


@router.get(
    "/",
    response_model=List[DriverAttendanceResponse],
    summary="List all driver attendance records",
)
def fetch_all_attendance(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return driver_attendance_service.get_all_attendance(db)


@router.get(
    "/{id}",
    response_model=DriverAttendanceResponse,
    summary="Get a single driver attendance record",
)
def fetch_attendance(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return driver_attendance_service.get_attendance(id, db)


@router.put(
    "/{id}",
    response_model=DriverAttendanceResponse,
    summary="Update a driver attendance record",
    description=(
        "Update the `attendance_status`, `check_in_time`, or `check_out_time` "
        "of an existing attendance record. The `driver_id` and `date` are "
        "immutable after creation."
    ),
)
def edit_attendance(
    id: int,
    payload: DriverAttendanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = driver_attendance_service.update_attendance(id, payload, db)
    log_action(db, action="UPDATE", resource="DriverAttendance", resource_id=res.id, details=f"Updated attendance ID {res.id} status to {res.attendance_status.value if hasattr(res.attendance_status, 'value') else res.attendance_status}", user=current_user)
    return res


@router.delete(
    "/{id}",
    summary="Delete a driver attendance record",
)
def remove_attendance(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = driver_attendance_service.delete_attendance(id, db)
    log_action(db, action="DELETE", resource="DriverAttendance", resource_id=id, details=f"Deleted attendance record with ID {id}", user=current_user)
    return res
