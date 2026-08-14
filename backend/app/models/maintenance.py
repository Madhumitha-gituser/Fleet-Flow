import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base


class MaintenanceCategory(str, enum.Enum):
    OIL_CHANGE = "Oil Change"
    TYRE_REPLACEMENT = "Tyre Replacement"
    BRAKE_SERVICE = "Brake Service"
    ENGINE_SERVICE = "Engine Service"
    GENERAL_INSPECTION = "General Inspection"


class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)

    category = Column(
        SQLEnum(MaintenanceCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    service_date = Column(Date, nullable=False)
    next_service_date = Column(Date, nullable=True)

    service_cost = Column(Float, nullable=True)
    service_provider = Column(String(255), nullable=True)

    status = Column(
        SQLEnum(MaintenanceStatus, values_callable=lambda x: [e.value for e in x]),
        default=MaintenanceStatus.SCHEDULED,
        nullable=False,
        index=True
    )

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenances")
    alerts = relationship("MaintenanceAlert", back_populates="maintenance", cascade="all, delete-orphan")
