import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from fastapi import HTTPException, status

from app.models.driver import Driver
from app.models.trip import Trip, TripStatus

logger = logging.getLogger("fleetflow.driver_performance_service")

# ---------------------------------------------------------------------------
# Task 6 – Active trip statuses (per spec)
# ---------------------------------------------------------------------------
_ACTIVE_STATUSES = {
    TripStatus.CREATED.value,
    TripStatus.ASSIGNED.value,
    TripStatus.IN_TRANSIT.value,
    # The spec also mentions "Picked Up" and "Out for Delivery", but the current
    # TripStatus enum does not include these values.  They are listed here as
    # comments for future extensibility.
    # "Picked Up",
    # "Out for Delivery",
}


def get_driver_performance(driver_id: int, db: Session) -> dict:
    """Dynamically calculate trip performance stats for a driver.

    Values are computed on-the-fly from the Trip table and are NEVER stored
    in the database (Task 6 requirement).
    """
    # Verify driver exists
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        logger.warning("get_driver_performance — driver %d not found", driver_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    # Pull all trips for this driver in a single query using conditional aggregation
    result = db.query(
        func.count(Trip.id).label("total_trips"),
        func.sum(
            case((Trip.trip_status == TripStatus.DELIVERED.value, 1), else_=0)
        ).label("completed_trips"),
        func.sum(
            case(
                (Trip.trip_status.in_(list(_ACTIVE_STATUSES)), 1),
                else_=0,
            )
        ).label("active_trips"),
        func.sum(
            case((Trip.trip_status == TripStatus.CANCELLED.value, 1), else_=0)
        ).label("cancelled_trips"),
    ).filter(Trip.driver_id == driver_id).one()

    total = result.total_trips or 0
    completed = result.completed_trips or 0
    active = result.active_trips or 0
    cancelled = result.cancelled_trips or 0

    logger.info(
        "get_driver_performance — driver %d: total=%d completed=%d active=%d cancelled=%d",
        driver_id, total, completed, active, cancelled,
    )

    return {
        "driver_id": driver.id,
        "driver_name": driver.name,
        "total_trips": total,
        "completed_trips": completed,
        "active_trips": active,
        "cancelled_trips": cancelled,
    }
