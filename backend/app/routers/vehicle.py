from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleStatusUpdate
from app.utils.security import has_role
from app.services.vehicle_service import (
    create_vehicle,
    get_all_vehicles,
    get_vehicle,
    update_vehicle,
    update_vehicle_status,
    delete_vehicle,
)

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicle Management"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 6 – Swagger-enriched CRUD endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new vehicle",
    description=(
        "Register a new vehicle in the fleet.  \n\n"
        "**Validations:**\n"
        "- `vehicle_number` must be unique across all vehicles.\n"
        "- `registration_number` must be unique.\n"
        "- If `driver_id` is supplied it must reference an existing driver (HTTP 404 otherwise).\n\n"
        "**Task 6:** Record is created successfully and the full `VehicleResponse` is returned."
    ),
)
def add_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    return create_vehicle(vehicle, db)


@router.get(
    "/",
    response_model=List[VehicleResponse],
    summary="List all vehicles",
    description="Retrieve the complete list of vehicles registered in the fleet.",
)
def fetch_all_vehicles(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return get_all_vehicles(db)


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Get a vehicle by ID",
    description=(
        "Fetch a single vehicle's details.  \n"
        "Returns **HTTP 404** when the `vehicle_id` does not exist — "
        "satisfying the invalid-vehicle-ID rejection requirement."
    ),
)
def fetch_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return get_vehicle(vehicle_id, db)


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Update all vehicle fields",
    description=(
        "Full update of an existing vehicle record. All fields are required.  \n"
        "Returns **HTTP 404** when `vehicle_id` does not exist.  \n"
        "Returns **HTTP 400** when duplicate `vehicle_number` or `registration_number` are supplied."
    ),
)
def edit_vehicle(
    vehicle_id: int,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    return update_vehicle(vehicle_id, vehicle, db)


# ---------------------------------------------------------------------------
# Task 5 – PATCH /vehicles/{vehicle_id}/status
# Update only the vehicle's operational status
# ---------------------------------------------------------------------------

@router.patch(
    "/{vehicle_id}/status",
    response_model=VehicleResponse,
    summary="Update vehicle status (Task 5)",
    description=(
        "Partially update **only** the operational status of a vehicle.  \n\n"
        "**Allowed status values:**\n"
        "- `Available` – vehicle is ready to be dispatched\n"
        "- `In Use` – vehicle is currently on a trip\n"
        "- `Under Maintenance` – vehicle is in the workshop\n"
        "- `Out of Service` – vehicle is decommissioned\n\n"
        "**Task 5 validations:**\n"
        "- Returns **HTTP 404** when `vehicle_id` does not exist.\n"
        "- Rejects invalid status strings at the schema level (HTTP 422).\n\n"
        "**Task 6 (Swagger):** Use the *Try it out* button below to verify that "
        "status updates correctly and that an invalid `vehicle_id` returns HTTP 404."
    ),
)
def patch_vehicle_status(
    vehicle_id: int,
    payload: VehicleStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    return update_vehicle_status(vehicle_id, payload, db)


@router.delete(
    "/{vehicle_id}",
    summary="Delete a vehicle",
    description=(
        "Remove a vehicle from the system.  \n"
        "Returns **HTTP 409 Conflict** if the vehicle has existing maintenance records — "
        "maintenance history is never deleted.  \n"
        "Consider setting the vehicle status to `'Out of Service'` instead."
    ),
)
def remove_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    return delete_vehicle(vehicle_id, db)