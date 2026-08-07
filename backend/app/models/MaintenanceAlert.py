import enum
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MaintenanceAlertStatus(str, enum.Enum):
	PENDING = "Pending"
	SENT = "Sent"
	COMPLETED = "Completed"


class MaintenanceAlert(Base):
	__tablename__ = "maintenance_alerts"

	id = Column(Integer, primary_key=True, index=True)
	vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
	maintenance_id = Column(Integer, ForeignKey("maintenance.id"), nullable=False)
	alert_message = Column(Text, nullable=False)
	alert_type = Column(String(100), nullable=False)
	alert_status = Column(
		SQLEnum(MaintenanceAlertStatus, values_callable=lambda x: [e.value for e in x]),
		default=MaintenanceAlertStatus.PENDING,
		nullable=False,
	)
	generated_date = Column(DateTime, default=datetime.utcnow, nullable=False)
	next_service_date = Column(Date, nullable=True)

	vehicle = relationship("Vehicle", back_populates="maintenance_alerts")
	maintenance = relationship("Maintenance", back_populates="alerts")
