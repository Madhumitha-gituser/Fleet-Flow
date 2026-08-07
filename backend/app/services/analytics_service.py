import math
from sqlalchemy.orm import Session

from app.models.shipment import Shipment, ShipmentStatus
from app.models.trip import Trip
from app.schemas.fuel_record import OperationalAnalyticsResponse


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def get_operational_analytics(db: Session) -> OperationalAnalyticsResponse:
    total_deliveries = db.query(Shipment).count()
    successful_deliveries = db.query(Shipment).filter(Shipment.current_status == ShipmentStatus.DELIVERED).count()
    delayed_deliveries = db.query(Shipment).filter(Shipment.current_status == ShipmentStatus.DELAYED).count()
    cancelled_deliveries = db.query(Shipment).filter(Shipment.current_status == ShipmentStatus.CANCELLED).count()

    trips = db.query(Trip).all()
    distances = []
    durations = []

    for t in trips:
        if (
            t.pickup_latitude is not None
            and t.pickup_longitude is not None
            and t.destination_latitude is not None
            and t.destination_longitude is not None
        ):
            dist = _haversine(
                t.pickup_latitude,
                t.pickup_longitude,
                t.destination_latitude,
                t.destination_longitude,
            )
            distances.append(dist)

        if t.scheduled_start_time and t.scheduled_end_time:
            dur_hours = (t.scheduled_end_time - t.scheduled_start_time).total_seconds() / 3600.0
            if dur_hours >= 0:
                durations.append(dur_hours)

    avg_distance = round(sum(distances) / len(distances), 2) if distances else 0.0
    avg_delivery_time = round(sum(durations) / len(durations), 2) if durations else 0.0

    return OperationalAnalyticsResponse(
        total_deliveries=total_deliveries,
        successful_deliveries=successful_deliveries,
        delayed_deliveries=delayed_deliveries,
        cancelled_deliveries=cancelled_deliveries,
        average_trip_distance=avg_distance,
        average_delivery_time=avg_delivery_time,
    )
