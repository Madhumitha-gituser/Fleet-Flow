"""
Tests for Tasks 4 (Driver Status Automation), 5 (Driver Attendance APIs),
6 (Driver Performance API) — Task 9 verification checklist.

Run from backend/ directory:
    pytest tests/test_driver_features.py -v

Prerequisites:
    A running PostgreSQL database reachable via DATABASE_URL in .env.
    At least one driver, vehicle, shipment and trip record, OR the fixtures
    create them automatically.
"""

import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.driver_assignment import DriverAssignment, AssignmentStatus
from app.models.driver_attendance import DriverAttendance, AttendanceStatus
from app.models.trip import Trip, TripStatus
from app.models.shipment import Shipment

from app.services import driver_assignment_service, driver_attendance_service
from app.services.driver_performance_service import get_driver_performance
from app.services.trip_service import _sync_driver_status_from_trip

from app.schemas.driver_assignment import DriverAssignmentCreate, DriverAssignmentUpdate
from app.schemas.driver_attendance import DriverAttendanceCreate, DriverAttendanceUpdate
from app.schemas.vehicle import VehicleCreate

client = TestClient(app, raise_server_exceptions=True)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db() -> Session:
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_driver_a(db: Session) -> Driver:
    """Return existing driver A (by license) or create one."""
    existing = db.query(Driver).filter(Driver.license_number == "LIC-TESTA-9001").first()
    if existing:
        return existing
    try:
        d = Driver(name="DriverA Test", license_number="LIC-TESTA-9001", phone="9000000001", status="Available")
        db.add(d)
        db.commit()
        db.refresh(d)
        return d
    except Exception:
        db.rollback()
        return db.query(Driver).filter(Driver.license_number == "LIC-TESTA-9001").first()


@pytest.fixture(scope="module")
def test_driver_b(db: Session) -> Driver:
    """Return existing driver B (by license) or create one."""
    existing = db.query(Driver).filter(Driver.license_number == "LIC-TESTB-9002").first()
    if existing:
        return existing
    try:
        d = Driver(name="DriverB Test", license_number="LIC-TESTB-9002", phone="9000000002", status="Available")
        db.add(d)
        db.commit()
        db.refresh(d)
        return d
    except Exception:
        db.rollback()
        return db.query(Driver).filter(Driver.license_number == "LIC-TESTB-9002").first()


@pytest.fixture(scope="module")
def test_vehicle_a(db: Session) -> Vehicle:
    """Return existing vehicle A (by vehicle_number) or create one."""
    existing = db.query(Vehicle).filter(Vehicle.vehicle_number == "TV-9001").first()
    if existing:
        return existing
    try:
        v = Vehicle(vehicle_number="TV-9001", registration_number="REG-TV9001",
                    vehicle_type="Truck", capacity=5000, fuel_type="Diesel", status="Available")
        db.add(v)
        db.commit()
        db.refresh(v)
        return v
    except Exception:
        db.rollback()
        return db.query(Vehicle).filter(Vehicle.vehicle_number == "TV-9001").first()


@pytest.fixture(scope="module")
def test_vehicle_b(db: Session) -> Vehicle:
    """Return existing vehicle B (by vehicle_number) or create one."""
    existing = db.query(Vehicle).filter(Vehicle.vehicle_number == "TV-9002").first()
    if existing:
        return existing
    try:
        v = Vehicle(vehicle_number="TV-9002", registration_number="REG-TV9002",
                    vehicle_type="Van", capacity=2000, fuel_type="Petrol", status="Available")
        db.add(v)
        db.commit()
        db.refresh(v)
        return v
    except Exception:
        db.rollback()
        return db.query(Vehicle).filter(Vehicle.vehicle_number == "TV-9002").first()


# ─────────────────────────────────────────────────────────────────────────────
# Task 4 – Driver Status Automation
# ─────────────────────────────────────────────────────────────────────────────

class TestTask4_DriverStatusAutomation:
    """Verify: Driver.status changes automatically with assignments/trips."""

    _assignment_id: int = None

    @staticmethod
    def _clear_active_assignments(db: Session, *driver_ids):
        """Remove all Active assignments for the given drivers to start clean."""
        for did in driver_ids:
            stale = db.query(DriverAssignment).filter(
                DriverAssignment.driver_id == did,
                DriverAssignment.assignment_status == AssignmentStatus.ACTIVE.value,
            ).all()
            for s in stale:
                db.delete(s)
        db.commit()

    def test_assignment_created_sets_driver_assigned(self, db, test_driver_a, test_vehicle_a):
        """Task 9 ✓: Driver assignment succeeds + driver status → Assigned."""
        # Ensure clean state
        self._clear_active_assignments(db, test_driver_a.id)
        test_driver_a.status = "Available"
        db.commit()

        payload = DriverAssignmentCreate(
            driver_id=test_driver_a.id,
            vehicle_id=test_vehicle_a.id,
            assignment_date=date.today(),
            assignment_status=AssignmentStatus.ACTIVE,
            remarks="test",
        )
        assignment = driver_assignment_service.create_assignment(payload, db)

        db.refresh(test_driver_a)
        assert assignment.assignment_status == AssignmentStatus.ACTIVE.value
        assert test_driver_a.status == "Assigned", (
            f"Expected 'Assigned', got '{test_driver_a.status}'"
        )
        # store assignment id for next tests
        TestTask4_DriverStatusAutomation._assignment_id = assignment.id

    def test_assignment_removed_sets_driver_available(self, db, test_driver_a):
        """Task 9 ✓: Driver status → Available when assignment is deleted."""
        driver_assignment_service.delete_assignment(
            TestTask4_DriverStatusAutomation._assignment_id, db
        )
        db.refresh(test_driver_a)
        assert test_driver_a.status == "Available", (
            f"Expected 'Available', got '{test_driver_a.status}'"
        )

    def test_assignment_fails_if_driver_unavailable(self, db, test_driver_a, test_vehicle_a, test_vehicle_b):
        """Task 9 ✓: Driver assignment fails if driver is already assigned."""
        from fastapi import HTTPException

        # Ensure clean slate: clear any leftover active assignments
        self._clear_active_assignments(db, test_driver_a.id)
        test_driver_a.status = "Available"
        db.commit()

        # First create an active assignment
        payload1 = DriverAssignmentCreate(
            driver_id=test_driver_a.id,
            vehicle_id=test_vehicle_a.id,
            assignment_date=date.today(),
            assignment_status=AssignmentStatus.ACTIVE,
        )
        a1 = driver_assignment_service.create_assignment(payload1, db)

        # Second create for same driver should fail
        payload2 = DriverAssignmentCreate(
            driver_id=test_driver_a.id,
            vehicle_id=test_vehicle_b.id,
            assignment_date=date.today(),
            assignment_status=AssignmentStatus.ACTIVE,
        )
        with pytest.raises(HTTPException) as exc_info:
            driver_assignment_service.create_assignment(payload2, db)

        assert exc_info.value.status_code == 400
        assert "already assigned" in exc_info.value.detail.lower()

        # Cleanup
        driver_assignment_service.delete_assignment(a1.id, db)

    def test_assignment_fails_if_vehicle_unavailable(self, db, test_driver_a, test_driver_b, test_vehicle_a):
        """Task 9 ✓: Driver assignment fails if vehicle is already assigned."""
        from fastapi import HTTPException

        # Ensure clean slate
        self._clear_active_assignments(db, test_driver_a.id, test_driver_b.id)
        test_driver_a.status = "Available"
        test_driver_b.status = "Available"
        db.commit()

        # First create an active assignment for driver_a with vehicle_a
        payload1 = DriverAssignmentCreate(
            driver_id=test_driver_a.id,
            vehicle_id=test_vehicle_a.id,
            assignment_date=date.today(),
            assignment_status=AssignmentStatus.ACTIVE,
        )
        a1 = driver_assignment_service.create_assignment(payload1, db)

        # Try to assign driver_b to the same vehicle
        payload2 = DriverAssignmentCreate(
            driver_id=test_driver_b.id,
            vehicle_id=test_vehicle_a.id,
            assignment_date=date.today(),
            assignment_status=AssignmentStatus.ACTIVE,
        )
        with pytest.raises(HTTPException) as exc_info:
            driver_assignment_service.create_assignment(payload2, db)

        assert exc_info.value.status_code == 400
        assert "already assigned" in exc_info.value.detail.lower()

        # Cleanup
        driver_assignment_service.delete_assignment(a1.id, db)

    def test_trip_status_assigned_sets_driver_assigned(self, db, test_driver_a):
        """Trip status Assigned → driver status Assigned."""
        test_driver_a.status = "Available"
        db.commit()

        mock_trip = type("Trip", (), {
            "driver_id": test_driver_a.id,
            "trip_status": TripStatus.ASSIGNED.value,
        })()

        _sync_driver_status_from_trip(mock_trip, db)
        db.commit()
        db.refresh(test_driver_a)
        assert test_driver_a.status == "Assigned"

    def test_trip_status_in_transit_sets_driver_on_trip(self, db, test_driver_a):
        """Trip status In Transit → driver status On Trip."""
        test_driver_a.status = "Assigned"
        db.commit()

        mock_trip = type("Trip", (), {
            "driver_id": test_driver_a.id,
            "trip_status": TripStatus.IN_TRANSIT.value,
        })()

        _sync_driver_status_from_trip(mock_trip, db)
        db.commit()
        db.refresh(test_driver_a)
        assert test_driver_a.status == "On Trip"

    def test_trip_status_delivered_sets_driver_available(self, db, test_driver_a):
        """Trip status Delivered → driver status Available."""
        test_driver_a.status = "On Trip"
        db.commit()

        mock_trip = type("Trip", (), {
            "driver_id": test_driver_a.id,
            "trip_status": TripStatus.DELIVERED.value,
        })()

        _sync_driver_status_from_trip(mock_trip, db)
        db.commit()
        db.refresh(test_driver_a)
        assert test_driver_a.status == "Available"

    def test_trip_status_cancelled_sets_driver_available(self, db, test_driver_a):
        """Trip status Cancelled → driver status Available."""
        test_driver_a.status = "On Trip"
        db.commit()

        mock_trip = type("Trip", (), {
            "driver_id": test_driver_a.id,
            "trip_status": TripStatus.CANCELLED.value,
        })()

        _sync_driver_status_from_trip(mock_trip, db)
        db.commit()
        db.refresh(test_driver_a)
        assert test_driver_a.status == "Available"


# ─────────────────────────────────────────────────────────────────────────────
# Task 5 – Driver Attendance APIs
# ─────────────────────────────────────────────────────────────────────────────

class TestTask5_DriverAttendanceAPIs:
    """Verify: Attendance CRUD + duplicate prevention."""

    _attendance_id: int = None

    def test_create_attendance_succeeds(self, db, test_driver_a):
        """Task 9 ✓: Attendance creation succeeds."""
        # Use a unique date that won't conflict
        test_date = date(2030, 1, 15)

        # Clean up any existing record first
        existing = db.query(DriverAttendance).filter(
            DriverAttendance.driver_id == test_driver_a.id,
            DriverAttendance.date == test_date,
        ).first()
        if existing:
            db.delete(existing)
            db.commit()

        payload = DriverAttendanceCreate(
            driver_id=test_driver_a.id,
            date=test_date,
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2030, 1, 15, 9, 0, 0),
        )
        record = driver_attendance_service.create_attendance(payload, db)

        assert record.id is not None
        assert record.driver_id == test_driver_a.id
        assert record.attendance_status == AttendanceStatus.PRESENT
        TestTask5_DriverAttendanceAPIs._attendance_id = record.id

    def test_duplicate_attendance_blocked(self, db, test_driver_a):
        """Task 9 ✓: Duplicate attendance blocked (same driver, same date)."""
        from fastapi import HTTPException

        payload = DriverAttendanceCreate(
            driver_id=test_driver_a.id,
            date=date(2030, 1, 15),  # same date as above
            attendance_status=AttendanceStatus.ABSENT,
        )
        with pytest.raises(HTTPException) as exc_info:
            driver_attendance_service.create_attendance(payload, db)

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail.lower()

    def test_get_attendance_by_id(self, db):
        """GET attendance by id returns correct record."""
        record = driver_attendance_service.get_attendance(
            TestTask5_DriverAttendanceAPIs._attendance_id, db
        )
        assert record.id == TestTask5_DriverAttendanceAPIs._attendance_id

    def test_get_all_attendance(self, db):
        """GET all attendance returns a list."""
        records = driver_attendance_service.get_all_attendance(db)
        assert isinstance(records, list)
        assert len(records) >= 1

    def test_update_attendance(self, db):
        """PUT attendance updates status."""
        payload = DriverAttendanceUpdate(
            attendance_status=AttendanceStatus.LEAVE,
        )
        updated = driver_attendance_service.update_attendance(
            TestTask5_DriverAttendanceAPIs._attendance_id, payload, db
        )
        assert updated.attendance_status == AttendanceStatus.LEAVE

    def test_delete_attendance(self, db):
        """DELETE attendance removes the record."""
        result = driver_attendance_service.delete_attendance(
            TestTask5_DriverAttendanceAPIs._attendance_id, db
        )
        assert "deleted" in result["message"].lower()

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            driver_attendance_service.get_attendance(
                TestTask5_DriverAttendanceAPIs._attendance_id, db
            )
        assert exc_info.value.status_code == 404

    def test_attendance_invalid_driver_returns_404(self, db):
        """POST with invalid driver_id returns 404."""
        from fastapi import HTTPException

        payload = DriverAttendanceCreate(
            driver_id=999999,
            date=date(2030, 2, 1),
            attendance_status=AttendanceStatus.PRESENT,
        )
        with pytest.raises(HTTPException) as exc_info:
            driver_attendance_service.create_attendance(payload, db)

        assert exc_info.value.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Task 6 – Driver Performance API
# ─────────────────────────────────────────────────────────────────────────────

class TestTask6_DriverPerformanceAPI:
    """Verify: Performance endpoint returns correct dynamic counts."""

    def test_performance_returns_correct_structure(self, db, test_driver_a):
        """Task 9 ✓: Performance API returns correct counts structure."""
        result = get_driver_performance(test_driver_a.id, db)

        assert "driver_id" in result
        assert "driver_name" in result
        assert "total_trips" in result
        assert "completed_trips" in result
        assert "active_trips" in result
        assert "cancelled_trips" in result

        assert result["driver_id"] == test_driver_a.id
        assert result["driver_name"] == test_driver_a.name

    def test_performance_counts_are_integers(self, db, test_driver_a):
        """All count fields must be integers >= 0."""
        result = get_driver_performance(test_driver_a.id, db)
        for field in ("total_trips", "completed_trips", "active_trips", "cancelled_trips"):
            assert isinstance(result[field], int), f"{field} is not int"
            assert result[field] >= 0, f"{field} is negative"

    def test_performance_total_equals_sum_of_parts(self, db, test_driver_a):
        """total_trips == completed + active + cancelled (+ any other future statuses)."""
        result = get_driver_performance(test_driver_a.id, db)
        classified = result["completed_trips"] + result["active_trips"] + result["cancelled_trips"]
        assert result["total_trips"] >= classified  # total can include created (unclassified) trips

    def test_performance_invalid_driver_returns_404(self, db):
        """GET performance for non-existent driver returns 404."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_driver_performance(999999, db)

        assert exc_info.value.status_code == 404

    def test_performance_with_real_trips(self, db, test_driver_a, test_vehicle_a):
        """Create actual trips and verify counts are accurate (Task 9 ✓)."""
        # Find an existing shipment or skip
        shipment = db.query(Shipment).first()
        if not shipment:
            pytest.skip("No shipment in DB — skipping trip-count accuracy test")

        # Reset driver
        test_driver_a.status = "Available"
        db.commit()

        initial = get_driver_performance(test_driver_a.id, db)

        # Insert a Delivered trip
        t1 = Trip(
            shipment_id=shipment.id,
            driver_id=test_driver_a.id,
            vehicle_id=test_vehicle_a.id,
            pickup_location="Loc A",
            destination="Loc B",
            scheduled_start_time=datetime(2030, 6, 1, 8, 0),
            scheduled_end_time=datetime(2030, 6, 1, 18, 0),
            trip_status=TripStatus.DELIVERED.value,
        )
        # Insert a Cancelled trip
        t2 = Trip(
            shipment_id=shipment.id,
            driver_id=test_driver_a.id,
            vehicle_id=test_vehicle_a.id,
            pickup_location="Loc C",
            destination="Loc D",
            scheduled_start_time=datetime(2030, 6, 2, 8, 0),
            scheduled_end_time=datetime(2030, 6, 2, 18, 0),
            trip_status=TripStatus.CANCELLED.value,
        )
        db.add_all([t1, t2])
        db.commit()

        after = get_driver_performance(test_driver_a.id, db)

        assert after["total_trips"] == initial["total_trips"] + 2
        assert after["completed_trips"] == initial["completed_trips"] + 1
        assert after["cancelled_trips"] == initial["cancelled_trips"] + 1

        # Cleanup
        db.delete(t1)
        db.delete(t2)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Task 7 – Swagger / HTTP-layer verification
# ─────────────────────────────────────────────────────────────────────────────

class TestTask7_SwaggerRoutes:
    """Verify all new routes appear in the OpenAPI schema."""

    def test_openapi_contains_driver_attendance(self):
        """Swagger shows Driver Attendance endpoints."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        paths = schema.get("paths", {})

        assert "/driver-attendance/" in paths, "POST/GET /driver-attendance/ not in OpenAPI"
        assert "/driver-attendance/{id}" in paths, "GET/PUT/DELETE /driver-attendance/{id} not in OpenAPI"

    def test_openapi_contains_driver_assignment(self):
        """Swagger shows Driver Assignment endpoints."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        paths = schema.get("paths", {})
        assert "/driver-assignments/" in paths
        assert "/driver-assignments/{assignment_id}" in paths

    def test_openapi_contains_driver_performance(self):
        """Swagger shows Driver Performance endpoint."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        paths = schema.get("paths", {})
        assert "/drivers/{driver_id}/performance" in paths, (
            "Performance endpoint not found in OpenAPI schema"
        )

    def test_driver_attendance_post_method_exists(self):
        resp = client.get("/openapi.json")
        paths = resp.json().get("paths", {})
        attendance_root = paths.get("/driver-attendance/", {})
        assert "post" in attendance_root, "POST method missing from /driver-attendance/"
        assert "get" in attendance_root, "GET method missing from /driver-attendance/"

    def test_driver_attendance_id_methods_exist(self):
        resp = client.get("/openapi.json")
        paths = resp.json().get("paths", {})
        attendance_id = paths.get("/driver-attendance/{id}", {})
        assert "get" in attendance_id, "GET /{id} missing"
        assert "put" in attendance_id, "PUT /{id} missing"
        assert "delete" in attendance_id, "DELETE /{id} missing"

    def test_driver_performance_get_method_exists(self):
        resp = client.get("/openapi.json")
        paths = resp.json().get("paths", {})
        perf = paths.get("/drivers/{driver_id}/performance", {})
        assert "get" in perf, "GET /drivers/{driver_id}/performance missing"
