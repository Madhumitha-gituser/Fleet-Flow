"""
Maintenance service layer.

Tasks covered
─────────────
• Task 3  – CRUD operations (create / read / update)
• Task 4  – Vehicle-ID validation (reject invalid IDs with HTTP 404;
             confirm record belongs to the correct vehicle)
• Task 5  – Auto-update vehicle status to "Under Maintenance" when a
             maintenance record with status "In Progress" is created
• Policy  – Maintenance history is NEVER physically deleted.
             Hard-delete is replaced by a `cancel_maintenance` soft-archive.
"""
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.vehicle import Vehicle
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_vehicle_or_404(vehicle_id: int, db: Session) -> Vehicle:
    """
    Fetch a Vehicle by PK; raise 404 if it does not exist.

    Task 4: used by create and the vehicle-scoped GET to enforce that
    invalid vehicle IDs are always rejected before any DB write or query.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Vehicle with id {vehicle_id} not found. "
                "Provide a valid vehicle_id."
            ),
        )
    return vehicle


def _get_maintenance_or_404(maintenance_id: int, db: Session) -> Maintenance:
    """Fetch a Maintenance record by PK; raise 404 if absent."""
    record = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with id {maintenance_id} not found.",
        )
    return record


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def create_maintenance(payload: MaintenanceCreate, db: Session) -> Maintenance:
    """
    Create a new maintenance record.

    Task 4 – Vehicle validation:
      • Verify the vehicle_id references an existing vehicle (404 if not).

    Task 5 – Auto-status:
      • If the new record status is "In Progress", the parent vehicle's
        status is automatically updated to "Under Maintenance".
    """
    # Task 4: validate vehicle exists first
    vehicle = _get_vehicle_or_404(payload.vehicle_id, db)

    db_record = Maintenance(
        vehicle_id=payload.vehicle_id,
        category=payload.category,
        service_date=payload.service_date,
        next_service_date=payload.next_service_date,
        service_cost=payload.service_cost,
        service_provider=payload.service_provider,
        status=payload.status,
        notes=payload.notes,
        created_at=datetime.utcnow(),
    )
    db.add(db_record)

    # Task 5: auto-update vehicle status when maintenance is in progress
    if payload.status == MaintenanceStatus.IN_PROGRESS:
        vehicle.status = "Under Maintenance"

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create maintenance record due to a database constraint.",
        ) from exc

    db.refresh(db_record)
    return db_record


def get_all_maintenance(db: Session) -> list[Maintenance]:
    """Return every maintenance record ordered by newest first."""
    return (
        db.query(Maintenance)
        .order_by(Maintenance.created_at.desc())
        .all()
    )


def get_maintenance_by_id(maintenance_id: int, db: Session) -> Maintenance:
    """Return a single maintenance record; 404 if not found."""
    return _get_maintenance_or_404(maintenance_id, db)


def get_maintenance_by_vehicle(vehicle_id: int, db: Session) -> list[Maintenance]:
    """
    Return all maintenance records that belong to a given vehicle.

    Task 4 – Vehicle validation:
      • Confirm the vehicle exists before filtering (404 for invalid vehicle IDs).
    """
    _get_vehicle_or_404(vehicle_id, db)
    return (
        db.query(Maintenance)
        .filter(Maintenance.vehicle_id == vehicle_id)
        .order_by(Maintenance.created_at.desc())
        .all()
    )


def update_maintenance(
    maintenance_id: int,
    payload: MaintenanceUpdate,
    db: Session,
) -> Maintenance:
    """
    Update an existing maintenance record.

    Note: vehicle_id is intentionally NOT part of MaintenanceUpdate —
    a maintenance record is permanently linked to the vehicle it was created for.

    Task 5 – Auto-status:
      • If status changes to "In Progress", parent vehicle is set to "Under Maintenance".
      • If status changes to "Completed" or "Cancelled", parent vehicle reverts to "Available"
        only when it has no other active maintenance records.
    """
    db_record = _get_maintenance_or_404(maintenance_id, db)

    old_status = db_record.status

    db_record.category = payload.category
    db_record.service_date = payload.service_date
    db_record.next_service_date = payload.next_service_date
    db_record.service_cost = payload.service_cost
    db_record.service_provider = payload.service_provider
    db_record.status = payload.status
    db_record.notes = payload.notes

    # Task 5: sync vehicle status based on maintenance status transition
    vehicle = db_record.vehicle
    if payload.status == MaintenanceStatus.IN_PROGRESS:
        vehicle.status = "Under Maintenance"
    elif payload.status in (MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED):
        # Revert vehicle to Available only if no other "In Progress" maintenance exists
        active = (
            db.query(Maintenance)
            .filter(
                Maintenance.vehicle_id == db_record.vehicle_id,
                Maintenance.id != maintenance_id,
                Maintenance.status == MaintenanceStatus.IN_PROGRESS,
            )
            .count()
        )
        if active == 0 and vehicle.status == "Under Maintenance":
            vehicle.status = "Available"

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update maintenance record due to a database constraint.",
        ) from exc

    db.refresh(db_record)
    return db_record


# ---------------------------------------------------------------------------
# Policy: maintenance history is NEVER deleted
# ---------------------------------------------------------------------------

def cancel_maintenance(maintenance_id: int, db: Session) -> Maintenance:
    """
    Soft-cancel a maintenance record by setting its status to 'Cancelled'.

    Maintenance history must NEVER be physically deleted — this is the
    only supported way to retire a record.

    Raises:
      • 404 if the record does not exist.
      • 409 if the record is already Completed (cannot be undone).
    """
    db_record = _get_maintenance_or_404(maintenance_id, db)

    if db_record.status == MaintenanceStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Maintenance record {maintenance_id} is already Completed "
                "and cannot be cancelled."
            ),
        )

    db_record.status = MaintenanceStatus.CANCELLED

    # Task 5: if vehicle was "Under Maintenance" due to this record, revert it
    vehicle = db_record.vehicle
    active = (
        db.query(Maintenance)
        .filter(
            Maintenance.vehicle_id == db_record.vehicle_id,
            Maintenance.id != maintenance_id,
            Maintenance.status == MaintenanceStatus.IN_PROGRESS,
        )
        .count()
    )
    if active == 0 and vehicle.status == "Under Maintenance":
        vehicle.status = "Available"

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not cancel maintenance record due to a database constraint.",
        ) from exc

    db.refresh(db_record)
    return db_record
