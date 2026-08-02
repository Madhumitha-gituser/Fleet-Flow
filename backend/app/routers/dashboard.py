"""
Dashboard router — GET /dashboard/summary and GET /dashboard/fleet
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.shipment import Shipment, ShipmentStatus
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.trip import Trip, TripStatus
from app.schemas.fuel_record import FleetDashboardResponse
from app.utils.security import has_role

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


ALLOWED_ROLES = ["Admin", "Dispatcher", "Fleet Manager", "Driver", "admin", "dispatcher", "fleet manager", "driver"]

# Statuses that count toward "active deliveries"
_ACTIVE_STATUSES = (
    ShipmentStatus.ASSIGNED,
    ShipmentStatus.PICKED_UP,
    ShipmentStatus.IN_TRANSIT,
    ShipmentStatus.OUT_FOR_DELIVERY,
)


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES)),
):
    """
    Return a summary of shipment counts for the dashboard.
    """
    total_shipments: int = db.query(func.count(Shipment.id)).scalar() or 0

    active_deliveries: int = (
        db.query(func.count(Shipment.id))
        .filter(Shipment.current_status.in_(_ACTIVE_STATUSES))
        .scalar() or 0
    )

    delivered_shipments: int = (
        db.query(func.count(Shipment.id))
        .filter(Shipment.current_status == ShipmentStatus.DELIVERED)
        .scalar() or 0
    )

    delayed_shipments: int = (
        db.query(func.count(Shipment.id))
        .filter(Shipment.current_status == ShipmentStatus.DELAYED)
        .scalar() or 0
    )

    return {
        "total_shipments": total_shipments,
        "active_deliveries": active_deliveries,
        "delivered_shipments": delivered_shipments,
        "delayed_shipments": delayed_shipments,
    }


@router.get(
    "/fleet",
    response_model=FleetDashboardResponse,
    summary="Get fleet performance dashboard",
    description=(
        "Calculate and return overall fleet performance dashboard metrics dynamically from the database.\n\n"
        "**Returned Metrics:**\n"
        "- Total Vehicles\n"
        "- Active Vehicles\n"
        "- Vehicles Under Maintenance\n"
        "- Total Drivers\n"
        "- Available Drivers\n"
        "- Assigned Drivers\n"
        "- Total Trips\n"
        "- Completed Trips\n"
        "- Active Shipments"
    ),
)
def get_fleet_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(has_role(ALLOWED_ROLES)),
):
    total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0
    active_vehicles = (
        db.query(func.count(Vehicle.id))
        .filter(func.lower(Vehicle.status).in_(["available", "in use", "active"]))
        .scalar() or 0
    )
    vehicles_under_maintenance = (
        db.query(func.count(Vehicle.id))
        .filter(func.lower(Vehicle.status) == "under maintenance")
        .scalar() or 0
    )

    total_drivers = db.query(func.count(Driver.id)).scalar() or 0
    available_drivers = (
        db.query(func.count(Driver.id))
        .filter(func.lower(Driver.status) == "available")
        .scalar() or 0
    )
    assigned_drivers = (
        db.query(func.count(Driver.id))
        .filter(func.lower(Driver.status).in_(["busy", "assigned", "on duty"]))
        .scalar() or 0
    )

    total_trips = db.query(func.count(Trip.id)).scalar() or 0
    completed_trips = (
        db.query(func.count(Trip.id))
        .filter(Trip.trip_status == TripStatus.DELIVERED)
        .scalar() or 0
    )

    active_shipments = (
        db.query(func.count(Shipment.id))
        .filter(Shipment.current_status.notin_([ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED]))
        .scalar() or 0
    )

    return FleetDashboardResponse(
        total_vehicles=total_vehicles,
        active_vehicles=active_vehicles,
        vehicles_under_maintenance=vehicles_under_maintenance,
        total_drivers=total_drivers,
        available_drivers=available_drivers,
        assigned_drivers=assigned_drivers,
        total_trips=total_trips,
        completed_trips=completed_trips,
        active_shipments=active_shipments,
    )
