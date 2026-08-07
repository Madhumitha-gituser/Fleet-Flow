from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.maintenance_alert import (
    MaintenanceAlertCreate,
    MaintenanceAlertResponse,
    MaintenanceAlertStatusUpdate,
)
from app.services import maintenance_alert_service
from app.utils.security import has_role

router = APIRouter(
    prefix="/maintenance-alerts",
    tags=["Maintenance Alerts"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


ALLOWED_READ_ROLES = ["Admin", "Fleet Manager", "Dispatcher", "admin", "fleet manager", "dispatcher"]
ALLOWED_WRITE_ROLES = ["Admin", "Fleet Manager", "admin", "fleet manager"]


@router.post(
    "/",
    response_model=MaintenanceAlertResponse,
    summary="Create a maintenance alert",
)
def create_alert(
    payload: MaintenanceAlertCreate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_WRITE_ROLES)),
):
    return maintenance_alert_service.create_alert(payload, db)


@router.get(
    "/",
    response_model=list[MaintenanceAlertResponse],
    summary="Get all maintenance alerts",
)
def get_all_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_READ_ROLES)),
):
    return maintenance_alert_service.get_all_alerts(db)


@router.get(
    "/{alert_id}",
    response_model=MaintenanceAlertResponse,
    summary="Get a maintenance alert by ID",
)
def get_alert_by_id(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_READ_ROLES)),
):
    return maintenance_alert_service.get_alert_by_id(alert_id, db)


@router.patch(
    "/{alert_id}/status",
    response_model=MaintenanceAlertResponse,
    summary="Update a maintenance alert status",
)
def update_alert_status(
    alert_id: int,
    payload: MaintenanceAlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_WRITE_ROLES)),
):
    return maintenance_alert_service.update_alert_status(alert_id, payload, db)


@router.delete(
    "/{alert_id}",
    summary="Delete a maintenance alert",
)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_WRITE_ROLES)),
):
    return maintenance_alert_service.delete_alert(alert_id, db)