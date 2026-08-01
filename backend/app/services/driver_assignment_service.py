import logging
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.trip import Trip
from app.models.driver_assignment import DriverAssignment, AssignmentStatus
from app.schemas.driver_assignment import DriverAssignmentCreate, DriverAssignmentUpdate

logger = logging.getLogger("fleetflow.driver_assignment_service")


# ---------------------------------------------------------------------------
# Helper — update Driver.status automatically (Task 4)
# ---------------------------------------------------------------------------

def _update_driver_status(driver: Driver, new_status: str, db: Session) -> None:
    """Automatically set Driver.status and commit; called whenever an assignment
    is created, updated, or removed so that no manual status update is needed."""
    driver.status = new_status
    db.add(driver)
    logger.info(
        "_update_driver_status — driver id=%d status → %s",
        driver.id, new_status,
    )


# ---------------------------------------------------------------------------
# Helper — check for an existing Active assignment
# ---------------------------------------------------------------------------

def _get_active_assignment_for_driver(driver_id: int, db: Session, exclude_id: int = None):
    """Return the first Active assignment for the given driver, optionally excluding one record."""
    q = db.query(DriverAssignment).filter(
        DriverAssignment.driver_id == driver_id,
        DriverAssignment.assignment_status == AssignmentStatus.ACTIVE.value,
    )
    if exclude_id:
        q = q.filter(DriverAssignment.id != exclude_id)
    return q.first()


def _get_active_assignment_for_vehicle(vehicle_id: int, db: Session, exclude_id: int = None):
    """Return the first Active assignment for the given vehicle, optionally excluding one record."""
    q = db.query(DriverAssignment).filter(
        DriverAssignment.vehicle_id == vehicle_id,
        DriverAssignment.assignment_status == AssignmentStatus.ACTIVE.value,
    )
    if exclude_id:
        q = q.filter(DriverAssignment.id != exclude_id)
    return q.first()


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def create_assignment(payload: DriverAssignmentCreate, db: Session):
    # 1 – Verify driver exists
    driver = db.query(Driver).filter(Driver.id == payload.driver_id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # 2 – Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # 3 – Verify trip exists (only when trip_id is provided)
    if payload.trip_id is not None:
        trip = db.query(Trip).filter(Trip.id == payload.trip_id).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    # 4 – Driver availability check
    if payload.assignment_status == AssignmentStatus.ACTIVE:
        active_driver = _get_active_assignment_for_driver(payload.driver_id, db)
        if active_driver:
            logger.warning(
                "create_assignment — driver %d already has active assignment %d",
                payload.driver_id, active_driver.id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver is already assigned.",
            )

        # 5 – Vehicle availability check
        active_vehicle = _get_active_assignment_for_vehicle(payload.vehicle_id, db)
        if active_vehicle:
            logger.warning(
                "create_assignment — vehicle %d already has active assignment %d",
                payload.vehicle_id, active_vehicle.id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehicle is already assigned.",
            )

    new_assignment = DriverAssignment(
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
        assignment_date=payload.assignment_date,
        assignment_status=payload.assignment_status.value,
        remarks=payload.remarks,
    )
    db.add(new_assignment)

    # ── Task 4: Auto-update driver status on assignment creation ──────────
    if payload.assignment_status == AssignmentStatus.ACTIVE:
        _update_driver_status(driver, "Assigned", db)

    db.commit()
    db.refresh(new_assignment)
    logger.info("create_assignment — created assignment id=%d", new_assignment.id)
    return new_assignment


def get_all_assignments(db: Session):
    assignments = db.query(DriverAssignment).all()
    logger.info("get_all_assignments — returned %d records", len(assignments))
    return assignments


def get_assignment(assignment_id: int, db: Session):
    assignment = db.query(DriverAssignment).filter(DriverAssignment.id == assignment_id).first()
    if not assignment:
        logger.warning("get_assignment — assignment %d not found", assignment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return assignment


def update_assignment(assignment_id: int, payload: DriverAssignmentUpdate, db: Session):
    db_assignment = get_assignment(assignment_id, db)

    # Remember the old driver so we can reset their status if driver changes
    old_driver_id = db_assignment.driver_id

    # 1 – Verify driver exists
    driver = db.query(Driver).filter(Driver.id == payload.driver_id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # 2 – Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # 3 – Verify trip exists (only when trip_id is provided)
    if payload.trip_id is not None:
        trip = db.query(Trip).filter(Trip.id == payload.trip_id).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    # 4 & 5 – Availability checks (only when setting status to Active)
    if payload.assignment_status == AssignmentStatus.ACTIVE:
        active_driver = _get_active_assignment_for_driver(
            payload.driver_id, db, exclude_id=assignment_id
        )
        if active_driver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Driver is already assigned.",
            )

        active_vehicle = _get_active_assignment_for_vehicle(
            payload.vehicle_id, db, exclude_id=assignment_id
        )
        if active_vehicle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehicle is already assigned.",
            )

    db_assignment.driver_id = payload.driver_id
    db_assignment.vehicle_id = payload.vehicle_id
    db_assignment.trip_id = payload.trip_id
    db_assignment.assignment_date = payload.assignment_date
    db_assignment.assignment_status = payload.assignment_status.value
    db_assignment.remarks = payload.remarks

    # ── Task 4: Auto-update driver status on assignment update ────────────
    if payload.assignment_status == AssignmentStatus.ACTIVE:
        _update_driver_status(driver, "Assigned", db)
    else:
        # Setting to Inactive or Completed → make driver Available
        # Also handle driver swap: reset the OLD driver if different
        if old_driver_id != payload.driver_id:
            old_driver = db.query(Driver).filter(Driver.id == old_driver_id).first()
            if old_driver:
                _update_driver_status(old_driver, "Available", db)
        _update_driver_status(driver, "Available", db)

    db.commit()
    db.refresh(db_assignment)
    logger.info("update_assignment — updated assignment id=%d", db_assignment.id)
    return db_assignment


def delete_assignment(assignment_id: int, db: Session):
    db_assignment = get_assignment(assignment_id, db)

    # ── Task 4: Auto-update driver status when assignment is removed ──────
    if db_assignment.assignment_status == AssignmentStatus.ACTIVE.value:
        driver = db.query(Driver).filter(Driver.id == db_assignment.driver_id).first()
        if driver:
            _update_driver_status(driver, "Available", db)

    db.delete(db_assignment)
    db.commit()
    logger.info("delete_assignment — deleted assignment id=%d", assignment_id)
    return {"message": "Assignment deleted successfully"}
