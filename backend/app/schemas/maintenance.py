from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.maintenance import MaintenanceCategory, MaintenanceStatus


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class MaintenanceCreate(BaseModel):
    vehicle_id: int
    category: MaintenanceCategory
    service_date: date
    next_service_date: Optional[date] = None
    service_cost: Optional[float] = Field(default=None, ge=0)
    service_provider: Optional[str] = None
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    category: MaintenanceCategory
    service_date: date
    next_service_date: Optional[date] = None
    service_cost: Optional[float] = Field(default=None, ge=0)
    service_provider: Optional[str] = None
    status: MaintenanceStatus
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class MaintenanceResponse(BaseModel):
    id: int
    vehicle_id: int
    category: MaintenanceCategory
    service_date: date
    next_service_date: Optional[date]
    service_cost: Optional[float]
    service_provider: Optional[str]
    status: MaintenanceStatus
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
