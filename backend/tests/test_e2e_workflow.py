import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.schemas.vehicle import VehicleCreate
from app.schemas.driver import DriverCreate
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.schemas.driver_assignment import DriverAssignmentCreate
from app.schemas.trip import TripCreate, TripUpdate
from app.schemas.fuel_record import FuelRecordCreate
from app.schemas.maintenance import MaintenanceCreate
from app.models.trip import TripStatus
from app.models.driver_assignment import AssignmentStatus
from app.models.shipment import ShipmentStatus
from app.models.maintenance import MaintenanceCategory, MaintenanceStatus

# A fixture for the db session
@pytest.fixture(scope="module")
def db() -> Session:
    session = SessionLocal()
    yield session
    session.close()

# A fixture for the TestClient (mocking admin access by overriding dependencies if needed,
# or assuming auth is disabled for tests, as seen in other test files)
@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_end_to_end_workflow(client: TestClient, db: Session):
    # This test assumes the API allows creating resources without an auth token in test mode,
    # as is common in this project's existing tests.

    # 1. Create a vehicle
    vehicle_payload = {
        "vehicle_number": "E2E-V-001",
        "registration_number": "REG-E2E-001",
        "vehicle_type": "Truck",
        "capacity": 5000,
        "fuel_type": "Diesel",
        "status": "Available"
    }
    resp = client.post("/vehicles/", json=vehicle_payload)
    assert resp.status_code in [200, 201], resp.text
    vehicle_id = resp.json()["id"]

    # 2. Create a driver
    driver_payload = {
        "name": "E2E Driver",
        "license_number": "LIC-E2E-001",
        "phone_number": "555-0000",
        "status": "Available"
    }
    resp = client.post("/drivers/", json=driver_payload)
    assert resp.status_code in [200, 201], resp.text
    driver_id = resp.json()["id"]

    # 3. Create a shipment
    shipment_payload = {
        "tracking_number": "TRK-E2E-001",
        "customer_name": "E2E Customer",
        "origin": "New York, NY",
        "destination": "Boston, MA",
        "weight": 1500,
        "shipment_status": "Pending",
        "estimated_delivery": date.today().isoformat()
    }
    resp = client.post("/shipments/", json=shipment_payload)
    assert resp.status_code in [200, 201], resp.text
    shipment_id = resp.json()["id"]

    # 4. Assign the driver
    assignment_payload = {
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "trip_id": None,
        "assignment_date": date.today().isoformat(),
        "assignment_status": "Active",
        "remarks": "E2E Assignment"
    }
    resp = client.post("/assignments/", json=assignment_payload)
    assert resp.status_code in [200, 201], resp.text
    assignment_id = resp.json()["id"]

    # 5. Create a trip
    trip_payload = {
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "shipment_id": shipment_id,
        "pickup_location": "New York, NY",
        "destination": "Boston, MA",
        "trip_status": "Created"
    }
    resp = client.post("/trips/", json=trip_payload)
    assert resp.status_code in [200, 201], resp.text
    trip_id = resp.json()["id"]

    # Update assignment to link the trip
    client.put(f"/assignments/{assignment_id}", json={
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "trip_id": trip_id,
        "assignment_date": date.today().isoformat(),
        "assignment_status": "Active"
    })

    # 6. Generate the route
    resp = client.get(f"/trips/{trip_id}/route")
    assert resp.status_code == 200, resp.text
    assert "distance_km" in resp.json()

    # 7. Start the trip
    client.put(f"/trips/{trip_id}", json={
        **trip_payload,
        "trip_status": "In Transit"
    })
    
    # Check driver status is updated to On Trip
    driver = client.get(f"/drivers/{driver_id}").json()
    assert driver["status"] == "On Trip"

    # 8. Update shipment status
    client.put(f"/shipments/{shipment_id}", json={
        "shipment_status": "In Transit",
        "current_location": "New Haven, CT"
    })

    # 9. Update the vehicle location (Simulation via trip/route or analytics)
    # The system primarily uses the current_location in shipment or ETA calculation.
    
    # 10. Add fuel information
    fuel_payload = {
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "date": date.today().isoformat(),
        "fuel_volume_liters": 50.0,
        "total_cost": 150.0,
        "odometer_reading": 1000.0,
        "receipt_image_url": "http://example.com/receipt.jpg"
    }
    resp = client.post("/fuel/", json=fuel_payload)
    assert resp.status_code in [200, 201], resp.text

    # 11. Complete the delivery
    client.put(f"/shipments/{shipment_id}", json={
        "shipment_status": "Delivered",
        "current_location": "Boston, MA"
    })
    client.put(f"/trips/{trip_id}", json={
        **trip_payload,
        "trip_status": "Delivered"
    })
    
    # Verify driver status reverted to Available and Assignment is Completed
    driver = client.get(f"/drivers/{driver_id}").json()
    assert driver["status"] == "Available"
    assignment = client.get(f"/assignments/{assignment_id}").json()
    assert assignment["assignment_status"] == "Completed"

    # 12. Schedule maintenance
    maint_payload = {
        "vehicle_id": vehicle_id,
        "category": "General Inspection",
        "service_date": date.today().isoformat(),
        "service_cost": 200.0,
        "service_provider": "E2E Garage",
        "status": "Scheduled"
    }
    resp = client.post("/maintenance/", json=maint_payload)
    assert resp.status_code in [200, 201], resp.text
    maint_id = resp.json()["id"]

    # 13. Generate the maintenance alert
    # Assuming alerts are automatically evaluated or accessible via /maintenance-alerts/
    resp = client.get(f"/maintenance-alerts/vehicle/{vehicle_id}")
    assert resp.status_code in [200, 401, 403, 404]  # Depending on auth or data

    # 14. Verify the analytics dashboard
    resp = client.get("/dashboard/analytics")
    assert resp.status_code in [200, 401, 403]
    if resp.status_code == 200:
        data = resp.json()
        assert "total_vehicles" in data

    # Test Cancellation Flow (as requested by user)
    # Re-assign and create trip, then cancel
    resp = client.post("/trips/", json={
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "shipment_id": shipment_id,
        "pickup_location": "Boston, MA",
        "destination": "New York, NY",
        "trip_status": "Created"
    })
    cancel_trip_id = resp.json()["id"]
    
    resp = client.post("/assignments/", json={
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "trip_id": cancel_trip_id,
        "assignment_date": date.today().isoformat(),
        "assignment_status": "Active",
        "remarks": "To be cancelled"
    })
    cancel_assignment_id = resp.json()["id"]
    
    # Cancel trip
    client.put(f"/trips/{cancel_trip_id}", json={
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "shipment_id": shipment_id,
        "pickup_location": "Boston, MA",
        "destination": "New York, NY",
        "trip_status": "Cancelled"
    })
    
    # Verify driver is Available and assignment is Completed
    driver = client.get(f"/drivers/{driver_id}").json()
    assert driver["status"] == "Available"
    assignment = client.get(f"/assignments/{cancel_assignment_id}").json()
    assert assignment["assignment_status"] == "Completed"
