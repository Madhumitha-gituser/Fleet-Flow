from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.maintenance_alert import MaintenanceReportResponse
from app.services import maintenance_service
from app.utils.security import has_role

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


ALLOWED_ROLES = ["Admin", "Fleet Manager", "Dispatcher", "Driver", "admin", "fleet manager", "dispatcher", "driver"]


@router.get(
    "/maintenance",
    response_model=MaintenanceReportResponse,
    summary="Get maintenance report",
    description=(
        "Return dynamic maintenance metrics from the existing maintenance table.\n\n"
        "Returned metrics:\n"
        "- Total Maintenance Records\n"
        "- Vehicles Under Maintenance\n"
        "- Completed Services\n"
        "- Overdue Services\n"
        "- Total Maintenance Cost\n"
        "- Most Frequent Maintenance Category"
    ),
)
def get_maintenance_report(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES)),
):
    return maintenance_service.get_maintenance_report(db)