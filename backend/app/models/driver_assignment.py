import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class AssignmentStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    COMPLETED = "Completed"


class DriverAssignment(Base):
    __tablename__ = "driver_assignments"

    id = Column(Integer, primary_key=True, index=True)

    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    # trip_id is nullable — an assignment may be created before or independent of a trip
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)

    assignment_date = Column(Date, nullable=False)
    assignment_status = Column(String(50), default=AssignmentStatus.ACTIVE.value, nullable=False)
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    driver = relationship("Driver", back_populates="assignments")
    vehicle = relationship("Vehicle", back_populates="assignments")
    trip = relationship("Trip", back_populates="driver_assignment")
