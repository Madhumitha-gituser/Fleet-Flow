"""
Pytest test suite for:
  - Fuel Monitoring APIs (CRUD & Validations)
  - Fuel Analytics API (GET /analytics/fuel)
  - Fleet Performance Dashboard API (GET /dashboard/fleet)
  - Operational Analytics API (GET /analytics/operations)

Run from backend/ directory:
    ..\venv\Scripts\python.exe -m pytest tests/test_fuel_analytics_dashboard.py -v
"""

from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.fuel_record import FuelRecord
from app.utils.security import get_current_user
from app.models.user import User


@pytest.fixture(scope="module")
def db() -> Session:
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def mock_admin_user() -> User:
    return User(id=999, name="Test Admin", email="admin@test.com", role="Admin")


@pytest.fixture(scope="module")
def client(mock_admin_user: User) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def sample_vehicle(db: Session) -> Vehicle:
    v = db.query(Vehicle).first()
    if not v:
        v = Vehicle(
            vehicle_number="TEST-FUEL-V1",
            registration_number="REG-FUEL-V1",
            vehicle_type="Truck",
            capacity=2000,
            fuel_type="Diesel",
            status="Available",
        )
        db.add(v)
        db.commit()
        db.refresh(v)
    return v


@pytest.fixture(scope="module")
def sample_driver(db: Session) -> Driver:
    d = db.query(Driver).first()
    if not d:
        d = Driver(
            name="Test Fuel Driver",
            license_number="LIC-FUEL-9999",
            phone="9876543210",
            status="Available",
        )
        db.add(d)
        db.commit()
        db.refresh(d)
    return d


class TestFuelMonitoringAPIs:

    def test_add_fuel_record_invalid_vehicle_rejected(self, client: TestClient, sample_driver: Driver):
        payload = {
            "vehicle_id": 999999,
            "driver_id": sample_driver.id,
            "fuel_quantity": 50.0,
            "fuel_cost": 100.0,
            "odometer_reading": 12000.0,
            "fuel_date": str(date.today()),
        }
        res = client.post("/fuel-records/", json=payload)
        assert res.status_code == 404
        assert "Vehicle with ID 999999 does not exist" in res.json()["detail"]

    def test_add_fuel_record_invalid_driver_rejected(self, client: TestClient, sample_vehicle: Vehicle):
        payload = {
            "vehicle_id": sample_vehicle.id,
            "driver_id": 999999,
            "fuel_quantity": 50.0,
            "fuel_cost": 100.0,
            "odometer_reading": 12000.0,
            "fuel_date": str(date.today()),
        }
        res = client.post("/fuel-records/", json=payload)
        assert res.status_code == 404
        assert "Driver with ID 999999 does not exist" in res.json()["detail"]

    def test_add_fuel_record_invalid_quantity_rejected(self, client: TestClient, sample_vehicle: Vehicle, sample_driver: Driver):
        payload = {
            "vehicle_id": sample_vehicle.id,
            "driver_id": sample_driver.id,
            "fuel_quantity": 0.0,  # <= 0
            "fuel_cost": 100.0,
            "odometer_reading": 12000.0,
            "fuel_date": str(date.today()),
        }
        res = client.post("/fuel-records/", json=payload)
        assert res.status_code in (400, 422)

    def test_add_fuel_record_invalid_cost_rejected(self, client: TestClient, sample_vehicle: Vehicle, sample_driver: Driver):
        payload = {
            "vehicle_id": sample_vehicle.id,
            "driver_id": sample_driver.id,
            "fuel_quantity": 50.0,
            "fuel_cost": -10.0,  # <= 0
            "odometer_reading": 12000.0,
            "fuel_date": str(date.today()),
        }
        res = client.post("/fuel-records/", json=payload)
        assert res.status_code in (400, 422)

    def test_add_and_crud_fuel_record_lifecycle(self, client: TestClient, sample_vehicle: Vehicle, sample_driver: Driver):
        # 1. Add
        payload = {
            "vehicle_id": sample_vehicle.id,
            "driver_id": sample_driver.id,
            "fuel_quantity": 40.0,
            "fuel_cost": 120.0,
            "odometer_reading": 15000.0,
            "fuel_date": str(date.today()),
            "fuel_station": "Shell Station",
            "remarks": "Pytest creation",
        }
        res_post = client.post("/fuel-records/", json=payload)
        assert res_post.status_code == 201
        data = res_post.json()
        record_id = data["id"]
        assert data["fuel_quantity"] == 40.0
        assert data["fuel_cost"] == 120.0

        # 2. View all
        res_all = client.get("/fuel-records/")
        assert res_all.status_code == 200
        records = res_all.json()
        assert any(r["id"] == record_id for r in records)

        # 3. Get by ID
        res_get = client.get(f"/fuel-records/{record_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == record_id

        # 4. Update
        update_payload = {
            "fuel_quantity": 45.0,
            "fuel_cost": 135.0,
            "remarks": "Updated by pytest",
        }
        res_put = client.put(f"/fuel-records/{record_id}", json=update_payload)
        assert res_put.status_code == 200
        updated_data = res_put.json()
        assert updated_data["fuel_quantity"] == 45.0
        assert updated_data["fuel_cost"] == 135.0
        assert updated_data["remarks"] == "Updated by pytest"

        # 5. Delete
        res_del = client.delete(f"/fuel-records/{record_id}")
        assert res_del.status_code == 200

        # 6. Verify deletion
        res_get_del = client.get(f"/fuel-records/{record_id}")
        assert res_get_del.status_code == 404


class TestAnalyticsAndDashboardAPIs:

    def test_get_fuel_analytics(self, client: TestClient):
        res = client.get("/analytics/fuel")
        assert res.status_code == 200
        data = res.json()
        assert "total_fuel_consumed" in data
        assert "total_fuel_cost" in data
        assert "average_fuel_consumption" in data
        assert "vehicle_with_highest_fuel_usage" in data
        assert "vehicle_with_lowest_fuel_usage" in data

    def test_get_fleet_dashboard(self, client: TestClient):
        res = client.get("/dashboard/fleet")
        assert res.status_code == 200
        data = res.json()
        assert "total_vehicles" in data
        assert "active_vehicles" in data
        assert "vehicles_under_maintenance" in data
        assert "total_drivers" in data
        assert "available_drivers" in data
        assert "assigned_drivers" in data
        assert "total_trips" in data
        assert "completed_trips" in data
        assert "active_shipments" in data

    def test_get_operational_analytics(self, client: TestClient):
        res = client.get("/analytics/operations")
        assert res.status_code == 200
        data = res.json()
        assert "total_deliveries" in data
        assert "successful_deliveries" in data
        assert "delayed_deliveries" in data
        assert "cancelled_deliveries" in data
        assert "average_trip_distance" in data
        assert "average_delivery_time" in data
