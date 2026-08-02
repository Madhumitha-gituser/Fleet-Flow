from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.fuel_record import FuelRecord
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.schemas.fuel_record import (
    FuelRecordCreate,
    FuelRecordUpdate,
    FuelAnalyticsResponse,
    VehicleFuelUsage,
)


def _validate_vehicle_and_driver(vehicle_id: int, driver_id: int, db: Session):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} does not exist."
        )

    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} does not exist."
        )


def create_fuel_record(payload: FuelRecordCreate, db: Session) -> FuelRecord:
    if payload.fuel_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fuel quantity must be greater than zero."
        )
    if payload.fuel_cost <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fuel cost must be greater than zero."
        )

    _validate_vehicle_and_driver(payload.vehicle_id, payload.driver_id, db)

    db_record = FuelRecord(
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        fuel_quantity=payload.fuel_quantity,
        fuel_cost=payload.fuel_cost,
        odometer_reading=payload.odometer_reading,
        fuel_date=payload.fuel_date,
        fuel_station=payload.fuel_station,
        remarks=payload.remarks,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_all_fuel_records(db: Session) -> List[FuelRecord]:
    return db.query(FuelRecord).order_by(FuelRecord.id.desc()).all()


def get_fuel_record_by_id(record_id: int, db: Session) -> FuelRecord:
    record = db.query(FuelRecord).filter(FuelRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fuel record with ID {record_id} not found."
        )
    return record


def update_fuel_record(record_id: int, payload: FuelRecordUpdate, db: Session) -> FuelRecord:
    record = get_fuel_record_by_id(record_id, db)

    target_vehicle_id = payload.vehicle_id if payload.vehicle_id is not None else record.vehicle_id
    target_driver_id = payload.driver_id if payload.driver_id is not None else record.driver_id
    _validate_vehicle_and_driver(target_vehicle_id, target_driver_id, db)

    if payload.fuel_quantity is not None:
        if payload.fuel_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fuel quantity must be greater than zero."
            )
        record.fuel_quantity = payload.fuel_quantity

    if payload.fuel_cost is not None:
        if payload.fuel_cost <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fuel cost must be greater than zero."
            )
        record.fuel_cost = payload.fuel_cost

    if payload.vehicle_id is not None:
        record.vehicle_id = payload.vehicle_id
    if payload.driver_id is not None:
        record.driver_id = payload.driver_id
    if payload.odometer_reading is not None:
        record.odometer_reading = payload.odometer_reading
    if payload.fuel_date is not None:
        record.fuel_date = payload.fuel_date
    if payload.fuel_station is not None:
        record.fuel_station = payload.fuel_station
    if payload.remarks is not None:
        record.remarks = payload.remarks

    db.commit()
    db.refresh(record)
    return record


def delete_fuel_record(record_id: int, db: Session) -> dict:
    record = get_fuel_record_by_id(record_id, db)
    db.delete(record)
    db.commit()
    return {"message": f"Fuel record {record_id} deleted successfully."}


def get_fuel_analytics(db: Session) -> FuelAnalyticsResponse:
    total_consumed_res = db.query(func.sum(FuelRecord.fuel_quantity)).scalar()
    total_consumed = float(total_consumed_res) if total_consumed_res is not None else 0.0

    total_cost_res = db.query(func.sum(FuelRecord.fuel_cost)).scalar()
    total_cost = float(total_cost_res) if total_cost_res is not None else 0.0

    avg_consumed_res = db.query(func.avg(FuelRecord.fuel_quantity)).scalar()
    avg_consumed = float(avg_consumed_res) if avg_consumed_res is not None else 0.0

    # Highest fuel usage vehicle
    highest_row = (
        db.query(FuelRecord.vehicle_id, func.sum(FuelRecord.fuel_quantity).label("total_fuel"))
        .group_by(FuelRecord.vehicle_id)
        .order_by(func.sum(FuelRecord.fuel_quantity).desc())
        .first()
    )

    highest_usage_vehicle: Optional[VehicleFuelUsage] = None
    if highest_row:
        v = db.query(Vehicle).filter(Vehicle.id == highest_row.vehicle_id).first()
        highest_usage_vehicle = VehicleFuelUsage(
            vehicle_id=highest_row.vehicle_id,
            vehicle_number=v.vehicle_number if v else None,
            registration_number=v.registration_number if v else None,
            total_fuel_consumed=round(float(highest_row.total_fuel), 2),
        )

    # Lowest fuel usage vehicle
    lowest_row = (
        db.query(FuelRecord.vehicle_id, func.sum(FuelRecord.fuel_quantity).label("total_fuel"))
        .group_by(FuelRecord.vehicle_id)
        .order_by(func.sum(FuelRecord.fuel_quantity).asc())
        .first()
    )

    lowest_usage_vehicle: Optional[VehicleFuelUsage] = None
    if lowest_row:
        v = db.query(Vehicle).filter(Vehicle.id == lowest_row.vehicle_id).first()
        lowest_usage_vehicle = VehicleFuelUsage(
            vehicle_id=lowest_row.vehicle_id,
            vehicle_number=v.vehicle_number if v else None,
            registration_number=v.registration_number if v else None,
            total_fuel_consumed=round(float(lowest_row.total_fuel), 2),
        )

    return FuelAnalyticsResponse(
        total_fuel_consumed=round(total_consumed, 2),
        total_fuel_cost=round(total_cost, 2),
        average_fuel_consumption=round(avg_consumed, 2),
        vehicle_with_highest_fuel_usage=highest_usage_vehicle,
        vehicle_with_lowest_fuel_usage=lowest_usage_vehicle,
    )
