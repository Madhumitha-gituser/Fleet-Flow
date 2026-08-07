from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.driver_assignment import (
    DriverAssignmentCreate,
    DriverAssignmentUpdate,
    DriverAssignmentResponse,
)
from app.services import driver_assignment_service
from app.utils.security import has_role
from app.utils.audit_log import log_action

router = APIRouter(
    prefix="/driver-assignments",
    tags=["Driver Assignment Management"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=DriverAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a driver to a vehicle and trip",
    description=(
        "Create a new driver assignment.  \n\n"
        "**Business rules:**\n"
        "- `driver_id`, `vehicle_id` must reference existing records.\n"
        "- If `trip_id` is provided it must reference an existing trip.\n"
        "- If the driver already has an **Active** assignment → HTTP 400 *Driver is already assigned.*\n"
        "- If the vehicle already has an **Active** assignment → HTTP 400 *Vehicle is already assigned.*"
    ),
)
def add_assignment(
    payload: DriverAssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = driver_assignment_service.create_assignment(payload, db)
    log_action(db, action="CREATE", resource="DriverAssignment", resource_id=res.id, details=f"Assigned driver ID {res.driver_id} to vehicle ID {res.vehicle_id}", user=current_user)
    return res


@router.get(
    "/",
    response_model=List[DriverAssignmentResponse],
    summary="List all driver assignments",
)
def fetch_all_assignments(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return driver_assignment_service.get_all_assignments(db)


@router.get(
    "/{assignment_id}",
    response_model=DriverAssignmentResponse,
    summary="Get a driver assignment by ID",
)
def fetch_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager", "Dispatcher"])),
):
    return driver_assignment_service.get_assignment(assignment_id, db)


@router.put(
    "/{assignment_id}",
    response_model=DriverAssignmentResponse,
    summary="Update a driver assignment",
    description=(
        "Update an existing assignment.  \n\n"
        "**Business rules:** Same availability checks as POST apply when "
        "setting `assignment_status` to **Active**. "
        "The current record is excluded from the conflict check so its own "
        "driver/vehicle are not treated as conflicting."
    ),
)
def edit_assignment(
    assignment_id: int,
    payload: DriverAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = driver_assignment_service.update_assignment(assignment_id, payload, db)
    log_action(db, action="UPDATE", resource="DriverAssignment", resource_id=res.id, details=f"Updated assignment ID {res.id} status to {res.assignment_status.value if hasattr(res.assignment_status, 'value') else res.assignment_status}", user=current_user)
    return res


@router.delete(
    "/{assignment_id}",
    summary="Delete a driver assignment",
)
def remove_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"])),
):
    res = driver_assignment_service.delete_assignment(assignment_id, db)
    log_action(db, action="DELETE", resource="DriverAssignment", resource_id=assignment_id, details=f"Deleted driver assignment with ID {assignment_id}", user=current_user)
    return res
