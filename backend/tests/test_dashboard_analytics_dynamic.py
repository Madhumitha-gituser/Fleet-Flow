import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.trip import Trip, TripStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.models.fuel_record import FuelRecord
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

def test_fleet_dashboard_dynamic_update(client: TestClient, db: Session):
    # Get initial counts
    res_initial = client.get("/dashboard/fleet")
    assert res_initial.status_code == 200
    initial_data = res_initial.json()
    
    # 1. Add a new active vehicle and a new available driver
    rand_id = str(uuid.uuid4())[:8]
    vehicle = Vehicle(
        vehicle_number=f"V-{rand_id}", registration_number=f"R-{rand_id}",
        vehicle_type="Truck", capacity=1000, fuel_type="Diesel", status="Available"
    )
    driver = Driver(
        name="Test Driver", license_number=f"L-{rand_id}", phone="12345", status="Available"
    )
    db.add(vehicle)
    db.add(driver)
    db.commit()
    db.refresh(vehicle)
    db.refresh(driver)
    
    # Verify dashboard
    res_after_add = client.get("/dashboard/fleet")
    assert res_after_add.status_code == 200
    after_data = res_after_add.json()
    
    assert after_data["total_vehicles"] == initial_data["total_vehicles"] + 1
    assert after_data["active_vehicles"] == initial_data["active_vehicles"] + 1
    assert after_data["total_drivers"] == initial_data["total_drivers"] + 1
    assert after_data["available_drivers"] == initial_data["available_drivers"] + 1
    
    # 2. Put vehicle under maintenance
    vehicle.status = "Under Maintenance"
    db.commit()
    
    res_maintenance = client.get("/dashboard/fleet")
    assert res_maintenance.status_code == 200
    maint_data = res_maintenance.json()
    assert maint_data["active_vehicles"] == after_data["active_vehicles"] - 1
    assert maint_data["vehicles_under_maintenance"] == initial_data["vehicles_under_maintenance"] + 1
    
    # 3. Add Fuel Record
    fuel = FuelRecord(
        vehicle_id=vehicle.id, driver_id=driver.id, fuel_quantity=100.5, fuel_cost=200,
        odometer_reading=100, fuel_date=str(date.today()), fuel_station="Station A"
    )
    db.add(fuel)
    db.commit()
    
    res_fuel = client.get("/dashboard/fleet")
    fuel_data = res_fuel.json()
    assert abs(fuel_data["fuel_consumption"] - (initial_data["fuel_consumption"] + 100.5)) < 0.01

def test_operational_analytics_dynamic_update(client: TestClient, db: Session):
    res_initial = client.get("/analytics/operations")
    assert res_initial.status_code == 200
    initial_data = res_initial.json()
    
    rand_id = str(uuid.uuid4())[:8]
    shipment = Shipment(
        tracking_number=f"TRK-{rand_id}", sender_name="Sender", receiver_name="Receiver",
        pickup_location="A", delivery_location="B",
        weight=100, current_status=ShipmentStatus.DELIVERED
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    
    driver = Driver(name="Test", license_number=f"L-{rand_id}", phone="123", status="Available")
    vehicle = Vehicle(vehicle_number=f"V-{rand_id}", registration_number=f"R-{rand_id}", vehicle_type="Truck", capacity=100, fuel_type="Diesel", status="Available")
    db.add_all([driver, vehicle])
    db.commit()
    db.refresh(driver)
    db.refresh(vehicle)
    
    trip = Trip(
        shipment_id=shipment.id, driver_id=driver.id, vehicle_id=vehicle.id,
        pickup_location="A", destination="B",
        pickup_latitude=0.0, pickup_longitude=0.0, destination_latitude=1.0, destination_longitude=1.0,
        trip_status=TripStatus.DELIVERED,
        scheduled_start_time=datetime.utcnow(),
        scheduled_end_time=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(trip)
    db.commit()
    
    res_after = client.get("/analytics/operations")
    after_data = res_after.json()
    
    assert after_data["total_deliveries"] == initial_data["total_deliveries"] + 1
    assert after_data["successful_deliveries"] == initial_data["successful_deliveries"] + 1
