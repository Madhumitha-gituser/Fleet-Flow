from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.MaintenanceAlert import MaintenanceAlert, MaintenanceAlertStatus
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.vehicle import Vehicle
from app.schemas.maintenance_alert import MaintenanceAlertCreate, MaintenanceAlertStatusUpdate


def _get_vehicle_or_404(vehicle_id: int, db: Session) -> Vehicle:
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with id {vehicle_id} not found.",
        )
    return vehicle


def _get_maintenance_or_404(maintenance_id: int, db: Session) -> Maintenance:
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance record with id {maintenance_id} not found.",
        )
    return maintenance


def _get_alert_or_404(alert_id: int, db: Session) -> MaintenanceAlert:
    alert = db.query(MaintenanceAlert).filter(MaintenanceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance alert with id {alert_id} not found.",
        )
    return alert


def _pending_alert_exists(maintenance_id: int, db: Session, alert_id: int | None = None) -> bool:
    query = db.query(MaintenanceAlert).filter(
        MaintenanceAlert.maintenance_id == maintenance_id,
        MaintenanceAlert.alert_status == MaintenanceAlertStatus.PENDING,
    )
    if alert_id is not None:
        query = query.filter(MaintenanceAlert.id != alert_id)
    return db.query(query.exists()).scalar()


def create_alert(payload: MaintenanceAlertCreate, db: Session) -> MaintenanceAlert:
    _get_vehicle_or_404(payload.vehicle_id, db)
    maintenance = _get_maintenance_or_404(payload.maintenance_id, db)

    if maintenance.vehicle_id != payload.vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Maintenance record {payload.maintenance_id} does not belong to vehicle "
                f"{payload.vehicle_id}."
            ),
        )

    if payload.alert_status == MaintenanceAlertStatus.PENDING and _pending_alert_exists(payload.maintenance_id, db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending alert already exists for this maintenance schedule.",
        )

    alert = MaintenanceAlert(
        vehicle_id=payload.vehicle_id,
        maintenance_id=payload.maintenance_id,
        alert_message=payload.alert_message,
        alert_type=payload.alert_type,
        alert_status=payload.alert_status,
        generated_date=datetime.utcnow(),
        next_service_date=maintenance.next_service_date,
    )

    db.add(alert)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending alert already exists for this maintenance schedule.",
        ) from exc

    db.refresh(alert)
    return alert


def get_all_alerts(db: Session) -> list[MaintenanceAlert]:
    return db.query(MaintenanceAlert).order_by(MaintenanceAlert.generated_date.desc()).all()


def get_alert_by_id(alert_id: int, db: Session) -> MaintenanceAlert:
    return _get_alert_or_404(alert_id, db)


def update_alert_status(alert_id: int, payload: MaintenanceAlertStatusUpdate, db: Session) -> MaintenanceAlert:
    alert = _get_alert_or_404(alert_id, db)

    if payload.alert_status == MaintenanceAlertStatus.PENDING and _pending_alert_exists(alert.maintenance_id, db, alert_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending alert already exists for this maintenance schedule.",
        )

    alert.alert_status = payload.alert_status

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update maintenance alert due to a database constraint.",
        ) from exc

    db.refresh(alert)
    return alert


def delete_alert(alert_id: int, db: Session) -> dict:
    alert = _get_alert_or_404(alert_id, db)
    db.delete(alert)
    db.commit()
    return {"message": f"Maintenance alert {alert_id} deleted successfully."}


def generate_due_maintenance_alerts(db: Session, reminder_days: int = 7) -> int:
    today = date.today()
    created_count = 0

    maintenances = (
        db.query(Maintenance)
        .filter(Maintenance.next_service_date.isnot(None))
        .filter(Maintenance.status.notin_([MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED]))
        .all()
    )

    for maintenance in maintenances:
        if maintenance.next_service_date is None:
            continue

        days_until_service = (maintenance.next_service_date - today).days
        if days_until_service > reminder_days:
            continue

        if _pending_alert_exists(maintenance.id, db):
            continue

        alert_type = "Overdue Maintenance" if days_until_service < 0 else "Upcoming Maintenance"
        alert_message = (
            f"Vehicle {maintenance.vehicle_id} requires maintenance on "
            f"{maintenance.next_service_date.isoformat()}."
        )

        db.add(
            MaintenanceAlert(
                vehicle_id=maintenance.vehicle_id,
                maintenance_id=maintenance.id,
                alert_message=alert_message,
                alert_type=alert_type,
                alert_status=MaintenanceAlertStatus.PENDING,
                generated_date=datetime.utcnow(),
                next_service_date=maintenance.next_service_date,
            )
        )
        created_count += 1

    if created_count:
        db.commit()
    else:
        db.rollback()

    return created_count