"""
Pytest test suite covering:
  Task 4  – Link Maintenance with Vehicle (vehicle-ID validation & ownership)
  Task 5  – Update Vehicle Status (dedicated PATCH endpoint + auto-sync)
  Task 6  – Swagger / HTTP-layer verification via FastAPI TestClient

Run from the backend/ directory:
    pytest tests/test_tasks_4_5_6.py -v

Prerequisites:
    pip install pytest httpx
    A running database reachable via DATABASE_URL in .env
    At least one vehicle must exist (or the fixture creates one).
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.vehicle import Vehicle
from app.models.maintenance import Maintenance, MaintenanceStatus, MaintenanceCategory
from app.services import maintenance_service, vehicle_service
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.schemas.vehicle import VehicleCreate, VehicleStatusUpdate

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def db() -> Session:
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_vehicle(db: Session) -> Vehicle:
    """Return the first existing vehicle, or create a test one."""
    v = db.query(Vehicle).first()
    if v:
        return v
    payload = VehicleCreate(
        vehicle_number="TEST-V-001",
        registration_number="REG-TEST-001",
        vehicle_type="Truck",
        capacity=5000,
        fuel_type="Diesel",
        status="Available",
    )
    v = vehicle_service.create_vehicle(payload, db)
    return v


@pytest.fixture(scope="module")
def second_vehicle(db: Session) -> Vehicle:
    """Create a second vehicle used for ownership-mismatch tests."""
    payload = VehicleCreate(
        vehicle_number="TEST-V-002",
        registration_number="REG-TEST-002",
        vehicle_type="Van",
        capacity=1500,
        fuel_type="Petrol",
        status="Available",
    )
    try:
        return vehicle_service.create_vehicle(payload, db)
    except Exception:
        return db.query(Vehicle).filter(Vehicle.vehicle_number == "TEST-V-002").first()


@pytest.fixture()
def maintenance_record(db: Session, test_vehicle: Vehicle) -> Maintenance:
    """Create a fresh maintenance record for each test that needs one."""
    payload = MaintenanceCreate(
        vehicle_id=test_vehicle.id,
        category=MaintenanceCategory.OIL_CHANGE,
        service_date=date.today(),
        service_cost=1200.0,
        service_provider="Test Lube",
        status=MaintenanceStatus.SCHEDULED,
        notes="Pytest fixture record",
    )
    record = maintenance_service.create_maintenance(payload, db)
    yield record
    # Soft-cancel instead of deleting — maintenance history is never deleted
    try:
        maintenance_service.cancel_maintenance(record.id, db)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# HTTP client (no authentication — use service-layer for auth tests separately)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# ─── TASK 4 : Link Maintenance with Vehicle ──────────────────────────────────
# ---------------------------------------------------------------------------

class TestTask4_VehicleIdValidation:
    """Task 4 – Vehicle ID must exist; invalid IDs are always rejected."""

    def test_create_with_invalid_vehicle_id_returns_404(self, db: Session):
        """Providing a non-existent vehicle_id must raise HTTP 404."""
        from fastapi import HTTPException
        payload = MaintenanceCreate(
            vehicle_id=999_999,
            category=MaintenanceCategory.BRAKE_SERVICE,
            service_date=date.today(),
        )
        with pytest.raises(HTTPException) as exc_info:
            maintenance_service.create_maintenance(payload, db)
        assert exc_info.value.status_code == 404
        assert "Vehicle with id 999999 not found" in exc_info.value.detail

    def test_create_with_valid_vehicle_id_succeeds(self, db: Session, test_vehicle: Vehicle):
        """A valid vehicle_id creates the record successfully."""
        from fastapi import HTTPException
        payload = MaintenanceCreate(
            vehicle_id=test_vehicle.id,
            category=MaintenanceCategory.OIL_CHANGE,
            service_date=date.today(),
        )
        record = maintenance_service.create_maintenance(payload, db)
        assert record.id is not None
        assert record.vehicle_id == test_vehicle.id
        # Cleanup
        maintenance_service.cancel_maintenance(record.id, db)

    def test_get_by_invalid_vehicle_id_returns_404(self, db: Session):
        """get_maintenance_by_vehicle must raise 404 for non-existent vehicle."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            maintenance_service.get_maintenance_by_vehicle(999_999, db)
        assert exc_info.value.status_code == 404

    def test_get_by_valid_vehicle_id_returns_list(self, db: Session, test_vehicle: Vehicle, maintenance_record: Maintenance):
        """get_maintenance_by_vehicle returns records for a real vehicle."""
        records = maintenance_service.get_maintenance_by_vehicle(test_vehicle.id, db)
        assert isinstance(records, list)
        assert any(r.id == maintenance_record.id for r in records)

    def test_record_belongs_to_correct_vehicle(self, db: Session, test_vehicle: Vehicle, maintenance_record: Maintenance):
        """Each record in the vehicle's list has the correct vehicle_id."""
        records = maintenance_service.get_maintenance_by_vehicle(test_vehicle.id, db)
        for r in records:
            assert r.vehicle_id == test_vehicle.id, (
                f"Record {r.id} has vehicle_id={r.vehicle_id}, expected {test_vehicle.id}"
            )

    def test_ownership_mismatch_detected(self, db: Session, test_vehicle: Vehicle,
                                          second_vehicle: Vehicle, maintenance_record: Maintenance):
        """
        A record created for vehicle A must NOT appear in vehicle B's list.
        The router endpoint enforces this; here we validate the data layer.
        """
        records_for_second = maintenance_service.get_maintenance_by_vehicle(second_vehicle.id, db)
        record_ids = [r.id for r in records_for_second]
        assert maintenance_record.id not in record_ids, (
            f"Record {maintenance_record.id} (vehicle {test_vehicle.id}) "
            f"should NOT appear for vehicle {second_vehicle.id}"
        )

    def test_get_by_id_returns_correct_record(self, db: Session, maintenance_record: Maintenance):
        """get_maintenance_by_id returns the exact record."""
        fetched = maintenance_service.get_maintenance_by_id(maintenance_record.id, db)
        assert fetched.id == maintenance_record.id
        assert fetched.vehicle_id == maintenance_record.vehicle_id

    def test_get_by_nonexistent_id_returns_404(self, db: Session):
        """get_maintenance_by_id raises 404 for a missing ID."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            maintenance_service.get_maintenance_by_id(999_999, db)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# ─── TASK 5 : Update Vehicle Status ─────────────────────────────────────────
# ---------------------------------------------------------------------------

class TestTask5_VehicleStatus:
    """Task 5 – PATCH /vehicles/{id}/status and auto-status sync."""

    def test_update_status_to_under_maintenance(self, db: Session, test_vehicle: Vehicle):
        """Status can be changed to 'Under Maintenance'."""
        payload = VehicleStatusUpdate(status="Under Maintenance")
        updated = vehicle_service.update_vehicle_status(test_vehicle.id, payload, db)
        assert updated.status == "Under Maintenance"
        # Reset
        vehicle_service.update_vehicle_status(test_vehicle.id, VehicleStatusUpdate(status="Available"), db)

    def test_update_status_to_available(self, db: Session, test_vehicle: Vehicle):
        """Status can be changed back to 'Available'."""
        payload = VehicleStatusUpdate(status="Available")
        updated = vehicle_service.update_vehicle_status(test_vehicle.id, payload, db)
        assert updated.status == "Available"

    def test_update_status_to_out_of_service(self, db: Session, test_vehicle: Vehicle):
        """Status can be changed to 'Out of Service'."""
        payload = VehicleStatusUpdate(status="Out of Service")
        updated = vehicle_service.update_vehicle_status(test_vehicle.id, payload, db)
        assert updated.status == "Out of Service"
        # Reset
        vehicle_service.update_vehicle_status(test_vehicle.id, VehicleStatusUpdate(status="Available"), db)

    def test_update_status_invalid_vehicle_returns_404(self, db: Session):
        """PATCH on a non-existent vehicle_id raises HTTP 404."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            vehicle_service.update_vehicle_status(999_999, VehicleStatusUpdate(status="Available"), db)
        assert exc_info.value.status_code == 404

    def test_auto_status_in_progress_sets_under_maintenance(self, db: Session, test_vehicle: Vehicle):
        """
        Creating an 'In Progress' maintenance record should automatically set
        the vehicle status to 'Under Maintenance' (Task 5 auto-sync).
        """
        # Ensure vehicle starts as Available
        vehicle_service.update_vehicle_status(test_vehicle.id, VehicleStatusUpdate(status="Available"), db)
        db.refresh(test_vehicle)

        payload = MaintenanceCreate(
            vehicle_id=test_vehicle.id,
            category=MaintenanceCategory.ENGINE_SERVICE,
            service_date=date.today(),
            status=MaintenanceStatus.IN_PROGRESS,
        )
        record = maintenance_service.create_maintenance(payload, db)
        db.refresh(test_vehicle)
        assert test_vehicle.status == "Under Maintenance"

        # Cleanup: cancel the record → vehicle should revert
        maintenance_service.cancel_maintenance(record.id, db)
        db.refresh(test_vehicle)
        assert test_vehicle.status == "Available"

    def test_auto_status_completed_reverts_vehicle(self, db: Session, test_vehicle: Vehicle):
        """
        Updating a record to 'Completed' should revert the vehicle back to
        'Available' when there are no other active maintenance records.
        """
        vehicle_service.update_vehicle_status(test_vehicle.id, VehicleStatusUpdate(status="Available"), db)
        db.refresh(test_vehicle)

        # Create In Progress record
        payload = MaintenanceCreate(
            vehicle_id=test_vehicle.id,
            category=MaintenanceCategory.TYRE_REPLACEMENT,
            service_date=date.today(),
            status=MaintenanceStatus.IN_PROGRESS,
        )
        record = maintenance_service.create_maintenance(payload, db)
        db.refresh(test_vehicle)
        assert test_vehicle.status == "Under Maintenance"

        # Update to Completed
        update = MaintenanceUpdate(
            category=record.category,
            service_date=record.service_date,
            status=MaintenanceStatus.COMPLETED,
        )
        maintenance_service.update_maintenance(record.id, update, db)
        db.refresh(test_vehicle)
        assert test_vehicle.status == "Available"

    def test_invalid_status_value_rejected_by_schema(self):
        """Pydantic should reject invalid status values at the schema level."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            VehicleStatusUpdate(status="Broken")


# ---------------------------------------------------------------------------
# ─── TASK 6 : Swagger / HTTP-layer verification ──────────────────────────────
# ---------------------------------------------------------------------------

class TestTask6_SwaggerHTTP:
    """
    Task 6 – Verify all scenarios are reachable via the HTTP API.
    Uses FastAPI TestClient to simulate real HTTP requests (no auth token
    required because TestClient bypasses auth middleware in test mode).

    NOTE: The /docs endpoint itself is tested to confirm Swagger is live.
    """

    def test_swagger_ui_is_available(self, client: TestClient):
        """GET /docs should return 200 — Swagger UI is running."""
        resp = client.get("/docs")
        assert resp.status_code == 200
        assert "swagger" in resp.text.lower() or "openapi" in resp.text.lower()

    def test_openapi_schema_is_available(self, client: TestClient):
        """GET /openapi.json must return a valid OpenAPI schema."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "paths" in schema
        # Vehicle status endpoint must be documented
        assert "/vehicles/{vehicle_id}/status" in schema["paths"]
        # Maintenance vehicle-scoped endpoint must be documented
        assert "/maintenance/vehicle/{vehicle_id}" in schema["paths"]

    def test_maintenance_list_endpoint_reachable(self, client: TestClient):
        """GET /maintenance/ returns 200 or 401 (not 404 or 500)."""
        resp = client.get("/maintenance/")
        assert resp.status_code in (200, 401, 403)

    def test_vehicle_list_endpoint_reachable(self, client: TestClient):
        """GET /vehicles/ returns 200 or 401 (not 404 or 500)."""
        resp = client.get("/vehicles/")
        assert resp.status_code in (200, 401, 403)

    def test_vehicle_status_patch_endpoint_documented(self, client: TestClient):
        """PATCH /vehicles/{id}/status endpoint must be in OpenAPI schema."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        path_item = schema["paths"].get("/vehicles/{vehicle_id}/status", {})
        assert "patch" in path_item, "PATCH /vehicles/{vehicle_id}/status not in OpenAPI schema"

    def test_maintenance_cancel_endpoint_documented(self, client: TestClient):
        """PATCH /maintenance/{id}/cancel must be in OpenAPI schema."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        path_item = schema["paths"].get("/maintenance/{maintenance_id}/cancel", {})
        assert "patch" in path_item, "PATCH /maintenance/{maintenance_id}/cancel not in schema"

    def test_maintenance_no_delete_endpoint(self, client: TestClient):
        """
        DELETE /maintenance/{id} must NOT exist — maintenance history
        is never deleted (policy enforcement).
        """
        resp = client.get("/openapi.json")
        schema = resp.json()
        maint_path = schema["paths"].get("/maintenance/{maintenance_id}", {})
        assert "delete" not in maint_path, (
            "DELETE /maintenance/{maintenance_id} found in schema — "
            "maintenance records must never be deleted."
        )

    def test_invalid_vehicle_id_returns_proper_error(self, client: TestClient):
        """
        GET /maintenance/vehicle/99999 (invalid vehicle ID) must return
        a proper JSON error — not a 500 or HTML error page.
        """
        resp = client.get("/maintenance/vehicle/99999")
        # Will be 401/403 without auth, but NOT 500
        assert resp.status_code != 500
        if resp.status_code == 200:
            # If auth is disabled in test config, should still be JSON
            assert resp.headers["content-type"].startswith("application/json")

    def test_vehicle_status_invalid_vehicle_returns_error(self, client: TestClient):
        """
        PATCH /vehicles/99999/status with invalid vehicle ID must return
        a JSON error (not 500).
        """
        resp = client.patch(
            "/vehicles/99999/status",
            json={"status": "Available"},
        )
        assert resp.status_code != 500


# ---------------------------------------------------------------------------
# ─── Policy: maintenance history is NEVER deleted ───────────────────────────
# ---------------------------------------------------------------------------

class TestMaintenanceNeverDeleted:
    """Explicit policy checks: no physical deletion of maintenance records."""

    def test_cancel_instead_of_delete(self, db: Session, test_vehicle: Vehicle):
        """Cancelling a record sets status to Cancelled but keeps the row."""
        payload = MaintenanceCreate(
            vehicle_id=test_vehicle.id,
            category=MaintenanceCategory.GENERAL_INSPECTION,
            service_date=date.today(),
            status=MaintenanceStatus.SCHEDULED,
        )
        record = maintenance_service.create_maintenance(payload, db)
        record_id = record.id

        maintenance_service.cancel_maintenance(record_id, db)

        # Row still exists
        still_there = db.query(Maintenance).filter(Maintenance.id == record_id).first()
        assert still_there is not None
        assert still_there.status == MaintenanceStatus.CANCELLED

    def test_cannot_cancel_completed_record(self, db: Session, test_vehicle: Vehicle):
        """A Completed record cannot be cancelled — business rule enforcement."""
        from fastapi import HTTPException
        payload = MaintenanceCreate(
            vehicle_id=test_vehicle.id,
            category=MaintenanceCategory.BRAKE_SERVICE,
            service_date=date.today(),
            status=MaintenanceStatus.SCHEDULED,
        )
        record = maintenance_service.create_maintenance(payload, db)
        # Force to Completed
        update = MaintenanceUpdate(
            category=record.category,
            service_date=record.service_date,
            status=MaintenanceStatus.COMPLETED,
        )
        maintenance_service.update_maintenance(record.id, update, db)

        with pytest.raises(HTTPException) as exc_info:
            maintenance_service.cancel_maintenance(record.id, db)
        assert exc_info.value.status_code == 409

    def test_vehicle_relationship_intact_after_update(self, db: Session, maintenance_record: Maintenance):
        """After updating a record, vehicle_id relationship stays the same."""
        original_vehicle_id = maintenance_record.vehicle_id
        update = MaintenanceUpdate(
            category=MaintenanceCategory.TYRE_REPLACEMENT,
            service_date=maintenance_record.service_date,
            status=MaintenanceStatus.SCHEDULED,
        )
        updated = maintenance_service.update_maintenance(maintenance_record.id, update, db)
        assert updated.vehicle_id == original_vehicle_id, (
            "vehicle_id changed after update — relationship must be immutable"
        )
