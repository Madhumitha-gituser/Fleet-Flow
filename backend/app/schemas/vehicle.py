from typing import Literal

from pydantic import BaseModel, Field

# Allowed vehicle status values (used by both VehicleCreate, VehicleUpdate, VehicleStatusUpdate)
VEHICLE_STATUS_VALUES = Literal[
    "Available",
    "In Use",
    "Under Maintenance",
    "Out of Service",
]


class VehicleCreate(BaseModel):
    vehicle_number: str = Field(..., description="Unique vehicle identifier (e.g. 'TN-01-AB-1234')")
    registration_number: str = Field(..., description="Official registration plate number")
    vehicle_type: str = Field(..., description="Type of vehicle (e.g. Truck, Van, Tanker)")
    capacity: int = Field(..., gt=0, description="Load capacity in kg")
    fuel_type: str = Field(..., description="Fuel type (Diesel, Petrol, CNG, Electric)")
    status: VEHICLE_STATUS_VALUES = Field("Available", description="Operational status of the vehicle")
    driver_id: int | None = Field(None, description="ID of the assigned driver (optional)")


class VehicleUpdate(BaseModel):
    vehicle_number: str = Field(..., description="Unique vehicle identifier")
    registration_number: str = Field(..., description="Official registration plate number")
    vehicle_type: str = Field(..., description="Type of vehicle")
    capacity: int = Field(..., gt=0, description="Load capacity in kg")
    fuel_type: str = Field(..., description="Fuel type")
    status: VEHICLE_STATUS_VALUES = Field(..., description="Operational status of the vehicle")
    driver_id: int | None = Field(None, description="ID of the assigned driver (optional)")


# ---------------------------------------------------------------------------
# Task 5 – Dedicated status-update schema
# ---------------------------------------------------------------------------

class VehicleStatusUpdate(BaseModel):
    """Payload for PATCH /vehicles/{vehicle_id}/status (Task 5)."""

    status: VEHICLE_STATUS_VALUES = Field(
        ...,
        description=(
            "New operational status.  Allowed values: "
            "'Available', 'In Use', 'Under Maintenance', 'Out of Service'."
        ),
        examples=["Under Maintenance"],
    )


class VehicleResponse(BaseModel):
    id: int
    vehicle_number: str
    registration_number: str
    vehicle_type: str
    capacity: int
    fuel_type: str
    status: str
    driver_id: int | None

    class Config:
        from_attributes = True