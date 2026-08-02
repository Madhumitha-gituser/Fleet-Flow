from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Fuel Record Schemas
# ---------------------------------------------------------------------------

class FuelRecordCreate(BaseModel):
    vehicle_id: int
    driver_id: int
    fuel_quantity: float = Field(..., gt=0, description="Quantity of fuel consumed; must be > 0")
    fuel_cost: float = Field(..., gt=0, description="Total fuel cost; must be > 0")
    odometer_reading: float = Field(..., ge=0, description="Odometer reading at fueling")
    fuel_date: date
    fuel_station: Optional[str] = None
    remarks: Optional[str] = None


class FuelRecordUpdate(BaseModel):
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    fuel_quantity: Optional[float] = Field(None, gt=0, description="Quantity of fuel consumed; must be > 0")
    fuel_cost: Optional[float] = Field(None, gt=0, description="Total fuel cost; must be > 0")
    odometer_reading: Optional[float] = Field(None, ge=0)
    fuel_date: Optional[date] = None
    fuel_station: Optional[str] = None
    remarks: Optional[str] = None


class FuelRecordResponse(BaseModel):
    id: int
    vehicle_id: int
    driver_id: int
    fuel_quantity: float
    fuel_cost: float
    odometer_reading: float
    fuel_date: date
    fuel_station: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Fuel Analytics Schemas
# ---------------------------------------------------------------------------

class VehicleFuelUsage(BaseModel):
    vehicle_id: int
    vehicle_number: Optional[str] = None
    registration_number: Optional[str] = None
    total_fuel_consumed: float


class FuelAnalyticsResponse(BaseModel):
    total_fuel_consumed: float
    total_fuel_cost: float
    average_fuel_consumption: float
    vehicle_with_highest_fuel_usage: Optional[VehicleFuelUsage] = None
    vehicle_with_lowest_fuel_usage: Optional[VehicleFuelUsage] = None


# ---------------------------------------------------------------------------
# Fleet Performance Dashboard Schema
# ---------------------------------------------------------------------------

class FleetDashboardResponse(BaseModel):
    total_vehicles: int
    active_vehicles: int
    vehicles_under_maintenance: int
    total_drivers: int
    available_drivers: int
    assigned_drivers: int
    total_trips: int
    completed_trips: int
    active_shipments: int


# ---------------------------------------------------------------------------
# Operational Analytics Schema
# ---------------------------------------------------------------------------

class OperationalAnalyticsResponse(BaseModel):
    total_deliveries: int
    successful_deliveries: int
    delayed_deliveries: int
    cancelled_deliveries: int
    average_trip_distance: float
    average_delivery_time: float
