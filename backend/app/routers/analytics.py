from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.fuel_record import FuelAnalyticsResponse, OperationalAnalyticsResponse
from app.services import fuel_record_service, analytics_service
from app.utils.security import has_role

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


ALLOWED_ROLES = ["Admin", "Fleet Manager", "Dispatcher", "Driver", "admin", "fleet manager", "dispatcher", "driver"]


@router.get(
    "/fuel",
    response_model=FuelAnalyticsResponse,
    summary="Get fuel analytics",
    description=(
        "Calculate and return fuel consumption analytics dynamically from the `fuel_records` database table.\n\n"
        "**Returned Metrics:**\n"
        "- Total Fuel Consumed\n"
        "- Total Fuel Cost\n"
        "- Average Fuel Consumption\n"
        "- Vehicle with Highest Fuel Usage\n"
        "- Vehicle with Lowest Fuel Usage"
    ),
)
def get_fuel_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES)),
):
    return fuel_record_service.get_fuel_analytics(db)


@router.get(
    "/operations",
    response_model=OperationalAnalyticsResponse,
    summary="Get operational analytics",
    description=(
        "Calculate and return operational analytics dynamically from the `shipments` and `trips` database tables.\n\n"
        "**Returned Metrics:**\n"
        "- Total Deliveries\n"
        "- Successful Deliveries\n"
        "- Delayed Deliveries\n"
        "- Cancelled Deliveries\n"
        "- Average Trip Distance\n"
        "- Average Delivery Time"
    ),
)
def get_operational_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES)),
):
    return analytics_service.get_operational_analytics(db)
