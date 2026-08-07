import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from app.main import app
from app.database import SessionLocal
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.trip import Trip, TripStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.models.maintenance import Maintenance, MaintenanceCategory, MaintenanceStatus
import app.utils.security as security


class FakeAdminUser:
    role = "Admin"


@pytest.fixture(scope="function")
def db() -> Session:
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def auth_override():
    app.dependency_overrides[security.get_current_user] = lambda: FakeAdminUser()
    yield
    app.dependency_overrides.pop(security.get_current_user, None)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_vehicle_under_maintenance_cannot_be_assigned(client: TestClient, db: Session):
    uid = uuid.uuid4().hex[:8]
    # 1. Create a vehicle already under maintenance
    vehicle = Vehicle(
        vehicle_number=f"M-VEH-{uid}",
        registration_number=f"M-REG-{uid}",
        vehicle_type="Truck", capacity=1000, fuel_type="Diesel", status="Under Maintenance"
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    # 2. Create a driver
    driver = Driver(
        name="M Driver", license_number=f"M-LIC-{uid}", phone="12345", status="Available"
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)

    # 3. Try to assign driver to the maintenance vehicle
    payload = {
        "driver_id": driver.id,
        "vehicle_id": vehicle.id,
        "assignment_date": str(date.today()),
        "assignment_status": "Active"
    }
    response = client.post("/driver-assignments/", json=payload)
    assert response.status_code == 400
    assert "Vehicle is under maintenance" in response.json()["detail"]


def test_driver_already_assigned_cannot_receive_another_active_trip(client: TestClient, db: Session):
    uid = uuid.uuid4().hex[:8]
    # 1. Create driver and vehicle
    driver = Driver(
        name="T Driver", license_number=f"T-LIC-{uid}", phone="12345", status="Available"
    )
    vehicle = Vehicle(
        vehicle_number=f"T-VEH-{uid}",
        registration_number=f"T-REG-{uid}",
        vehicle_type="Truck", capacity=1000, fuel_type="Diesel", status="Available"
    )
    db.add(driver)
    db.add(vehicle)
    db.commit()
    db.refresh(driver)
    db.refresh(vehicle)

    # 2. Create a shipment
    shipment = Shipment(
        tracking_number=f"TRK-{uid}", sender_name="Sender", receiver_name="Receiver",
        pickup_location="A", delivery_location="B",
        weight=100, current_status=ShipmentStatus.CREATED
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # 3. Create an active trip for the driver
    trip1 = Trip(
        shipment_id=shipment.id, driver_id=driver.id, vehicle_id=vehicle.id,
        pickup_location="A", destination="B",
        pickup_latitude=0, pickup_longitude=0, destination_latitude=1, destination_longitude=1,
        trip_status=TripStatus.IN_TRANSIT,
        scheduled_start_time=datetime.utcnow(),
        scheduled_end_time=datetime.utcnow() + timedelta(days=1)
    )
    db.add(trip1)
    db.commit()

    # 4. Try to create a second active trip for the same driver via API
    payload = {
        "shipment_id": shipment.id,
        "driver_id": driver.id,
        "vehicle_id": vehicle.id,
        "pickup_location": "A",
        "destination": "B",
        "scheduled_start_time": str(datetime.utcnow()),
        "scheduled_end_time": str(datetime.utcnow() + timedelta(days=1))
    }
    response = client.post("/trips/", json=payload)
    assert response.status_code == 400
    assert "Driver already has an active trip" in response.json()["detail"]


def test_driver_on_leave_cannot_be_assigned(client: TestClient, db: Session):
    uid = uuid.uuid4().hex[:8]
    # 1. Create driver on leave
    driver = Driver(
        name="L Driver", license_number=f"L-LIC-{uid}", phone="12345", status="Leave"
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)

    # 2. Create vehicle
    vehicle = Vehicle(
        vehicle_number=f"L-VEH-{uid}",
        registration_number=f"L-REG-{uid}",
        vehicle_type="Truck", capacity=1000, fuel_type="Diesel", status="Available"
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    # 3. Try to assign the on-leave driver
    payload = {
        "driver_id": driver.id,
        "vehicle_id": vehicle.id,
        "assignment_date": str(date.today()),
        "assignment_status": "Active"
    }
    response = client.post("/driver-assignments/", json=payload)
    assert response.status_code == 400
    assert "Driver is on leave" in response.json()["detail"]


def test_fuel_records_cannot_be_created_for_invalid_vehicles(client: TestClient, db: Session):
    uid = uuid.uuid4().hex[:8]
    driver = Driver(
        name="F Driver", license_number=f"F-LIC-{uid}", phone="12345", status="Available"
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)

    payload = {
        "vehicle_id": 99999,  # invalid vehicle
        "driver_id": driver.id,
        "fuel_quantity": 50,
        "fuel_cost": 100,
        "odometer_reading": 1000,
        "fuel_date": str(date.today()),
        "fuel_station": "Station A"
    }
    response = client.post("/fuel-records/", json=payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_invalid_maintenance_records_return_proper_errors(client: TestClient, db: Session):
    payload = {
        "vehicle_id": 99999,  # invalid vehicle
        "category": MaintenanceCategory.OIL_CHANGE,
        "service_date": str(date.today()),
        "service_cost": 100,
        "status": MaintenanceStatus.SCHEDULED
    }
    response = client.post("/maintenance/", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
