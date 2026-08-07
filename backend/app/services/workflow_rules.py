from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.driver_attendance import DriverAttendance, AttendanceStatus
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.vehicle import Vehicle


def _status_text(value) -> str:
    return str(value or "").strip().lower()


def _driver_is_on_leave(driver: Driver, db: Session) -> bool:
    if _status_text(driver.status) in {"leave", "on leave"}:
        return True

    leave_record = (
        db.query(DriverAttendance.id)
        .filter(
            DriverAttendance.driver_id == driver.id,
            DriverAttendance.date == date.today(),
            DriverAttendance.attendance_status == AttendanceStatus.LEAVE,
        )
        .first()
    )
    return leave_record is not None


def _vehicle_is_under_maintenance(vehicle: Vehicle, db: Session) -> bool:
    if _status_text(vehicle.status) == "under maintenance":
        return True

    active_maintenance = (
        db.query(Maintenance.id)
        .filter(
            Maintenance.vehicle_id == vehicle.id,
            Maintenance.status == MaintenanceStatus.IN_PROGRESS,
        )
        .first()
    )
    return active_maintenance is not None


def ensure_driver_available(driver_id: int, db: Session) -> Driver:
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    if _driver_is_on_leave(driver, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver is on leave and cannot be assigned.",
        )

    return driver


def ensure_vehicle_available(vehicle_id: int, db: Session) -> Vehicle:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    if _vehicle_is_under_maintenance(vehicle, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle is under maintenance and cannot be assigned to a trip.",
        )

    return vehicle