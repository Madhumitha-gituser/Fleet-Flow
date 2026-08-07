from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.models.MaintenanceAlert import MaintenanceAlertStatus


class MaintenanceAlertCreate(BaseModel):
    vehicle_id: int
    maintenance_id: int
    alert_message: str
    alert_type: str
    alert_status: MaintenanceAlertStatus = MaintenanceAlertStatus.PENDING


class MaintenanceAlertStatusUpdate(BaseModel):
    alert_status: MaintenanceAlertStatus


class MaintenanceAlertResponse(BaseModel):
    id: int
    vehicle_id: int
    maintenance_id: int
    alert_message: str
    alert_type: str
    alert_status: MaintenanceAlertStatus
    generated_date: datetime
    next_service_date: Optional[date]

    class Config:
        from_attributes = True


class MaintenanceReportResponse(BaseModel):
    total_maintenance_records: int
    vehicles_under_maintenance: int
    completed_services: int
    overdue_services: int
    total_maintenance_cost: float
    most_frequent_maintenance_category: Optional[str]