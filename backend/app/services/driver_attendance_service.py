import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.driver_attendance import DriverAttendance
from app.schemas.driver_attendance import DriverAttendanceCreate, DriverAttendanceUpdate

logger = logging.getLogger("fleetflow.driver_attendance_service")


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def create_attendance(payload: DriverAttendanceCreate, db: Session):
    # 1 – Verify driver exists
    driver = db.query(Driver).filter(Driver.id == payload.driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # 2 – Enforce one attendance record per driver per date (Task 5 validation)
    existing = (
        db.query(DriverAttendance)
        .filter(
            DriverAttendance.driver_id == payload.driver_id,
            DriverAttendance.date == payload.date,
        )
        .first()
    )
    if existing:
        logger.warning(
            "create_attendance — duplicate attendance for driver %d on %s",
            payload.driver_id, payload.date,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Attendance for driver {payload.driver_id} on {payload.date} already exists.",
        )

    new_record = DriverAttendance(
        driver_id=payload.driver_id,
        date=payload.date,
        attendance_status=payload.attendance_status,
        check_in_time=payload.check_in_time,
        check_out_time=payload.check_out_time,
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    logger.info("create_attendance — created record id=%d", new_record.id)
    return new_record


def get_all_attendance(db: Session):
    records = db.query(DriverAttendance).all()
    logger.info("get_all_attendance — returned %d records", len(records))
    return records


def get_attendance(attendance_id: int, db: Session):
    record = db.query(DriverAttendance).filter(DriverAttendance.id == attendance_id).first()
    if not record:
        logger.warning("get_attendance — record %d not found", attendance_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )
    return record


def update_attendance(attendance_id: int, payload: DriverAttendanceUpdate, db: Session):
    record = get_attendance(attendance_id, db)

    record.attendance_status = payload.attendance_status
    record.check_in_time = payload.check_in_time
    record.check_out_time = payload.check_out_time

    db.commit()
    db.refresh(record)
    logger.info("update_attendance — updated record id=%d", record.id)
    return record


def delete_attendance(attendance_id: int, db: Session):
    record = get_attendance(attendance_id, db)
    db.delete(record)
    db.commit()
    logger.info("delete_attendance — deleted record id=%d", attendance_id)
    return {"message": "Attendance record deleted successfully"}
