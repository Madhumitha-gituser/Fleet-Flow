from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.fuel_record import (
    FuelRecordCreate,
    FuelRecordUpdate,
    FuelRecordResponse,
)
from app.services import fuel_record_service
from app.utils.security import has_role
from app.utils.audit_log import log_action

router = APIRouter(
    prefix="/fuel-records",
    tags=["Fuel Management"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


ALLOWED_ROLES_READ = ["Admin", "Fleet Manager", "Dispatcher", "Driver", "admin", "fleet manager", "dispatcher", "driver"]
ALLOWED_ROLES_WRITE = ["Admin", "Fleet Manager", "Dispatcher", "admin", "fleet manager", "dispatcher"]


@router.post(
    "/",
    response_model=FuelRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a fuel record",
    description=(
        "Record a new fuel transaction for a vehicle and driver.\n\n"
        "**Validations:**\n"
        "- Vehicle must exist in the database (404 error otherwise).\n"
        "- Driver must exist in the database (404 error otherwise).\n"
        "- Fuel quantity must be strictly greater than zero (400 or 422 error).\n"
        "- Fuel cost must be strictly greater than zero (400 or 422 error)."
    ),
)
def add_fuel_record(
    payload: FuelRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES_WRITE)),
):
    res = fuel_record_service.create_fuel_record(payload, db)
    log_action(db, action="CREATE", resource="FuelRecord", resource_id=res.id, details=f"Logged {res.fuel_quantity}L fuel costing ₹{res.fuel_cost} for vehicle ID {res.vehicle_id}", user=current_user)
    return res


@router.get(
    "/",
    response_model=List[FuelRecordResponse],
    summary="View all fuel records",
    description="Retrieve all fuel records stored in the database.",
)
def view_all_fuel_records(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES_READ)),
):
    return fuel_record_service.get_all_fuel_records(db)


@router.get(
    "/{record_id}",
    response_model=FuelRecordResponse,
    summary="Get fuel record by ID",
    description="Retrieve a single fuel record by its primary key ID.",
)
def get_fuel_record_by_id(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES_READ)),
):
    return fuel_record_service.get_fuel_record_by_id(record_id, db)


@router.put(
    "/{record_id}",
    response_model=FuelRecordResponse,
    summary="Update fuel record",
    description=(
        "Update an existing fuel record.\n\n"
        "**Validations:**\n"
        "- Record ID must exist.\n"
        "- If updated, vehicle and driver must exist.\n"
        "- If updated, fuel quantity and cost must be strictly greater than zero."
    ),
)
def update_fuel_record(
    record_id: int,
    payload: FuelRecordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES_WRITE)),
):
    res = fuel_record_service.update_fuel_record(record_id, payload, db)
    log_action(db, action="UPDATE", resource="FuelRecord", resource_id=res.id, details=f"Updated fuel record ID {res.id} for vehicle ID {res.vehicle_id}", user=current_user)
    return res


@router.delete(
    "/{record_id}",
    summary="Delete fuel record",
    description="Delete a fuel record from the database by ID.",
)
def delete_fuel_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES_WRITE)),
):
    res = fuel_record_service.delete_fuel_record(record_id, db)
    log_action(db, action="DELETE", resource="FuelRecord", resource_id=record_id, details=f"Deleted fuel record with ID {record_id}", user=current_user)
    return res
