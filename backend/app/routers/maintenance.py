"""
Maintenance Management Router

Tasks covered
─────────────
• Task 3  – Full CRUD (create / read / update)
• Task 4  – Vehicle-linked endpoints with vehicle-ID validation
• Task 5  – Vehicle status is automatically set to "Under Maintenance"
             when a maintenance record in status "In Progress" is created
• Task 6  – Every endpoint carries rich Swagger documentation so testers
             can exercise all scenarios directly from the /docs UI
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
)
from app.services import maintenance_service
from app.utils.security import has_role
from app.utils.audit_log import log_action

router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance Management"],
)


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 3 + Task 4 + Task 6 – Maintenance CRUD with Swagger docs
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a maintenance record (Task 3 / Task 4)",
    description=(
        "Create a new maintenance record for a vehicle.  \n\n"
        "**Task 4 – Vehicle validation:**\n"
        "- `vehicle_id` **must** reference an existing vehicle.\n"
        "- An invalid `vehicle_id` is rejected with **HTTP 404** and a descriptive error message.\n\n"
        "**Task 6 (Swagger):** Use *Try it out* to verify:\n"
        "1. A record is created successfully with a valid `vehicle_id`.\n"
        "2. An invalid `vehicle_id` (e.g. `99999`) returns HTTP 404."
    ),
)
def create_maintenance(
    payload: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = maintenance_service.create_maintenance(payload, db)
    log_action(db, action="CREATE", resource="Maintenance", resource_id=res.id, details=f"Created maintenance record for vehicle ID {res.vehicle_id} (Category: {res.category.value if hasattr(res.category, 'value') else res.category})", user=current_user)
    return res


@router.get(
    "/",
    response_model=List[MaintenanceResponse],
    summary="List all maintenance records",
    description=(
        "Retrieve every maintenance record across all vehicles, ordered newest first.  \n"
        "**Maintenance history is never deleted** — records are permanent."
    ),
)
def get_all_maintenance(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return maintenance_service.get_all_maintenance(db)


@router.get(
    "/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Get a maintenance record by ID",
    description=(
        "Retrieve a single maintenance record by its primary key.  \n"
        "Returns **HTTP 404** when the ID does not exist."
    ),
)
def get_maintenance_by_id(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return maintenance_service.get_maintenance_by_id(maintenance_id, db)


@router.put(
    "/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Update a maintenance record (Task 3)",
    description=(
        "Update an existing maintenance record.  \n\n"
        "**Note:** `vehicle_id` is intentionally excluded — a record is permanently "
        "linked to the vehicle it was created for.  \n"
        "**Task 6 (Swagger):** Verify that the vehicle relationship remains intact after update."
    ),
)
def update_maintenance(
    maintenance_id: int,
    payload: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = maintenance_service.update_maintenance(maintenance_id, payload, db)
    log_action(db, action="UPDATE", resource="Maintenance", resource_id=res.id, details=f"Updated maintenance record status to {res.status.value if hasattr(res.status, 'value') else res.status}", user=current_user)
    return res


# ---------------------------------------------------------------------------
# Policy: maintenance history must NEVER be deleted.
# The DELETE endpoint is intentionally absent.
# Instead we expose a PATCH archive endpoint that marks a record as Cancelled.
# ---------------------------------------------------------------------------

@router.patch(
    "/{maintenance_id}/cancel",
    response_model=MaintenanceResponse,
    summary="Cancel a maintenance record (never delete)",
    description=(
        "Mark a maintenance record as **Cancelled** without removing it from the database.  \n\n"
        "Maintenance history is **permanent** — records are never physically deleted "
        "to preserve the full service history of every vehicle.  \n"
        "Returns **HTTP 404** when the record does not exist.  \n"
        "Returns **HTTP 409** when the record is already Completed (cannot be cancelled)."
    ),
)
def cancel_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = maintenance_service.cancel_maintenance(maintenance_id, db)
    log_action(db, action="UPDATE", resource="Maintenance", resource_id=res.id, details="Cancelled maintenance record", user=current_user)
    return res


# ---------------------------------------------------------------------------
# Task 4 – Vehicle-scoped endpoints
# Validate vehicle existence; confirm record belongs to the correct vehicle
# ---------------------------------------------------------------------------

@router.get(
    "/vehicle/{vehicle_id}",
    response_model=List[MaintenanceResponse],
    summary="Get all maintenance records for a vehicle (Task 4)",
    description=(
        "Return all maintenance records that belong to the given vehicle, ordered newest first.  \n\n"
        "**Task 4 validations:**\n"
        "- Returns **HTTP 404** when `vehicle_id` does not exist.\n"
        "- Only records whose `vehicle_id` matches are returned.\n\n"
        "**Task 6 (Swagger):**\n"
        "1. Use a real vehicle ID — verify only that vehicle's records are returned.\n"
        "2. Use an invalid ID (e.g. `99999`) — verify HTTP 404 is returned."
    ),
)
def get_maintenance_by_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return maintenance_service.get_maintenance_by_vehicle(vehicle_id, db)


@router.get(
    "/vehicle/{vehicle_id}/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Get a specific maintenance record for a vehicle (Task 4)",
    description=(
        "Fetch a maintenance record by ID **and** verify it belongs to the given vehicle.  \n\n"
        "**Task 4 validations:**\n"
        "- Returns **HTTP 404** when the vehicle doesn't exist.\n"
        "- Returns **HTTP 400** when the record exists but does **not** belong to that vehicle.\n\n"
        "**Task 6 (Swagger):** Test ownership mismatch by passing a `maintenance_id` that "
        "belongs to a different vehicle — the API returns HTTP 400 with a clear message."
    ),
)
def get_maintenance_for_vehicle(
    vehicle_id: int,
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    # Task 4: first validate that the vehicle exists
    maintenance_service.get_maintenance_by_vehicle(vehicle_id, db)  # raises 404 if vehicle absent

    record = maintenance_service.get_maintenance_by_id(maintenance_id, db)

    # Task 4: validate ownership — record must belong to the requested vehicle
    if record.vehicle_id != vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Maintenance record {maintenance_id} does not belong to "
                f"vehicle {vehicle_id}."
            ),
        )
    return record
