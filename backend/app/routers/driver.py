from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from app.schemas.driver_performance import DriverPerformanceResponse
from app.utils.security import has_role
from app.utils.audit_log import log_action
from app.services.driver_service import (
    create_driver,
    get_all_drivers,
    get_driver,
    update_driver,
    delete_driver,
)
from app.services.driver_performance_service import get_driver_performance

router = APIRouter(
    prefix="/drivers",
    tags=["Driver Management"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=DriverResponse)
def add_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = create_driver(driver, db)
    log_action(db, action="CREATE", resource="Driver", resource_id=res.id, details=f"Created driver {res.name} (License: {res.license_number})", user=current_user)
    return res


@router.get("/", response_model=List[DriverResponse])
def fetch_all_drivers(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return get_all_drivers(db)


# ── Task 6: Driver Performance ─────────────────────────────────────────────
@router.get(
    "/{driver_id}/performance",
    response_model=DriverPerformanceResponse,
    tags=["Driver Performance"],
    summary="Get performance stats for a driver",
    description=(
        "Calculate and return trip statistics for a driver dynamically "
        "from the Trip table — **no stored values**.  \n\n"
        "**Definitions:**\n"
        "- `total_trips` — all trips for the driver\n"
        "- `completed_trips` — trips with status **Delivered**\n"
        "- `active_trips` — trips with status **Created**, **Assigned**, "
        "**Picked Up**, **In Transit**, or **Out for Delivery**\n"
        "- `cancelled_trips` — trips with status **Cancelled**"
    ),
)
def fetch_driver_performance(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return get_driver_performance(driver_id, db)


@router.get("/{driver_id}", response_model=DriverResponse)
def fetch_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return get_driver(driver_id, db)


@router.put("/{driver_id}", response_model=DriverResponse)
def edit_driver(
    driver_id: int,
    driver: DriverUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = update_driver(driver_id, driver, db)
    log_action(db, action="UPDATE", resource="Driver", resource_id=res.id, details=f"Updated driver {res.name} details", user=current_user)
    return res


@router.delete("/{driver_id}")
def remove_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = delete_driver(driver_id, db)
    log_action(db, action="DELETE", resource="Driver", resource_id=driver_id, details=f"Deleted driver with ID {driver_id}", user=current_user)
    return res