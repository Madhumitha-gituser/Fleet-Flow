import enum
from datetime import datetime

from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base


class AttendanceStatus(str, enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LEAVE = "Leave"


class DriverAttendance(Base):
    __tablename__ = "driver_attendances"

    # Task 5: enforce one attendance record per driver per date at DB level
    __table_args__ = (
        UniqueConstraint("driver_id", "date", name="uq_driver_attendances_driver_date"),
    )

    id = Column(Integer, primary_key=True, index=True)

    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)

    date = Column(Date, nullable=False)

    attendance_status = Column(
        SQLEnum(AttendanceStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    driver = relationship("Driver", back_populates="attendances")
