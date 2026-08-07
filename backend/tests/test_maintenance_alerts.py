from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.celery import celery_app, check_due_maintenance_alerts
from app.database import SessionLocal
from app.main import app
from app.models.MaintenanceAlert import MaintenanceAlert, MaintenanceAlertStatus
from app.models.maintenance import Maintenance, MaintenanceCategory, MaintenanceStatus
from app.models.vehicle import Vehicle
from app.schemas.maintenance import MaintenanceCreate
from app.schemas.maintenance_alert import MaintenanceAlertCreate, MaintenanceAlertStatusUpdate
from app.services import maintenance_alert_service, maintenance_service, vehicle_service
from app.services.maintenance_alert_service import generate_due_maintenance_alerts
from app.schemas.vehicle import VehicleCreate
import app.utils.security as security


class FakeAdminUser:
    role = "Admin"


@pytest.fixture(scope="module")
def db() -> Session:
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def auth_override():
    app.dependency_overrides[security.get_current_user] = lambda: FakeAdminUser()
    yield
    app.dependency_overrides.pop(security.get_current_user, None)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def alert_vehicle(db: Session) -> Vehicle:
    existing = db.query(Vehicle).filter(Vehicle.vehicle_number == "ALERT-VEH-1001").first()
    if existing:
        return existing

    payload = VehicleCreate(
        vehicle_number="ALERT-VEH-1001",
        registration_number="ALERT-REG-1001",
        vehicle_type="Truck",
        capacity=4000,
        fuel_type="Diesel",
        status="Available",
    )
    return vehicle_service.create_vehicle(payload, db)


@pytest.fixture(scope="module")
def due_maintenance(db: Session, alert_vehicle: Vehicle) -> Maintenance:
    existing = (
        db.query(Maintenance)
        .filter(
            Maintenance.vehicle_id == alert_vehicle.id,
            Maintenance.service_provider == "Alert Test Due",
        )
        .first()
    )
    if existing:
        return existing

    payload = MaintenanceCreate(
        vehicle_id=alert_vehicle.id,
        category=MaintenanceCategory.OIL_CHANGE,
        service_date=date.today() - timedelta(days=10),
        next_service_date=date.today() + timedelta(days=2),
        service_cost=250.0,
        service_provider="Alert Test Due",
        status=MaintenanceStatus.SCHEDULED,
        notes="Maintenance alert due test",
    )
    return maintenance_service.create_maintenance(payload, db)


@pytest.fixture(scope="module")
def completed_maintenance(db: Session, alert_vehicle: Vehicle) -> Maintenance:
    existing = (
        db.query(Maintenance)
        .filter(
            Maintenance.vehicle_id == alert_vehicle.id,
            Maintenance.service_provider == "Alert Test Completed",
        )
        .first()
    )
    if existing:
        return existing

    payload = MaintenanceCreate(
        vehicle_id=alert_vehicle.id,
        category=MaintenanceCategory.BRAKE_SERVICE,
        service_date=date.today() - timedelta(days=30),
        next_service_date=date.today() - timedelta(days=1),
        service_cost=375.0,
        service_provider="Alert Test Completed",
        status=MaintenanceStatus.COMPLETED,
        notes="Maintenance report test",
    )
    return maintenance_service.create_maintenance(payload, db)


def _cleanup_alerts_and_maintenance(db: Session, *records):
    alert_ids = [record.id for record in db.query(MaintenanceAlert).filter(MaintenanceAlert.maintenance_id.in_([r.id for r in records])).all()]
    if alert_ids:
        for alert in db.query(MaintenanceAlert).filter(MaintenanceAlert.id.in_(alert_ids)).all():
            db.delete(alert)

    for record in records:
        db.delete(record)
    db.commit()


def _clear_alerts_for_maintenance(db: Session, maintenance_id: int):
    alerts = db.query(MaintenanceAlert).filter(MaintenanceAlert.maintenance_id == maintenance_id).all()
    for alert in alerts:
        db.delete(alert)
    if alerts:
        db.commit()


def test_openapi_includes_maintenance_alert_and_report_paths(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/maintenance-alerts/" in schema["paths"]
    assert "/maintenance-alerts/{alert_id}" in schema["paths"]
    assert "/maintenance-alerts/{alert_id}/status" in schema["paths"]
    assert "/reports/maintenance" in schema["paths"]


def test_maintenance_alert_api_crud_flow(client: TestClient, db: Session, due_maintenance: Maintenance):
    _clear_alerts_for_maintenance(db, due_maintenance.id)

    payload = {
        "vehicle_id": due_maintenance.vehicle_id,
        "maintenance_id": due_maintenance.id,
        "alert_message": "Service due soon",
        "alert_type": "Upcoming Maintenance",
        "alert_status": "Pending",
    }

    create_response = client.post("/maintenance-alerts/", json=payload)
    assert create_response.status_code == 200 or create_response.status_code == 201
    created = create_response.json()
    alert_id = created["id"]
    assert created["alert_status"] == "Pending"

    list_response = client.get("/maintenance-alerts/")
    assert list_response.status_code == 200
    assert any(alert["id"] == alert_id for alert in list_response.json())

    detail_response = client.get(f"/maintenance-alerts/{alert_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == alert_id

    update_response = client.patch(
        f"/maintenance-alerts/{alert_id}/status",
        json={"alert_status": "Sent"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["alert_status"] == "Sent"

    delete_response = client.delete(f"/maintenance-alerts/{alert_id}")
    assert delete_response.status_code == 200
    assert "deleted successfully" in delete_response.json()["message"]


def test_maintenance_alert_validation_errors(client: TestClient, db: Session, due_maintenance: Maintenance):
    invalid_vehicle_response = client.post(
        "/maintenance-alerts/",
        json={
            "vehicle_id": 999999,
            "maintenance_id": due_maintenance.id,
            "alert_message": "Invalid vehicle",
            "alert_type": "Upcoming Maintenance",
            "alert_status": "Pending",
        },
    )
    assert invalid_vehicle_response.status_code == 404

    invalid_maintenance_response = client.post(
        "/maintenance-alerts/",
        json={
            "vehicle_id": due_maintenance.vehicle_id,
            "maintenance_id": 999999,
            "alert_message": "Invalid maintenance",
            "alert_type": "Upcoming Maintenance",
            "alert_status": "Pending",
        },
    )
    assert invalid_maintenance_response.status_code == 404


def test_duplicate_pending_alert_prevention(client: TestClient, db: Session, due_maintenance: Maintenance):
    _clear_alerts_for_maintenance(db, due_maintenance.id)

    first_response = client.post(
        "/maintenance-alerts/",
        json={
            "vehicle_id": due_maintenance.vehicle_id,
            "maintenance_id": due_maintenance.id,
            "alert_message": "First pending alert",
            "alert_type": "Upcoming Maintenance",
            "alert_status": "Pending",
        },
    )
    assert first_response.status_code in (200, 201)

    duplicate_response = client.post(
        "/maintenance-alerts/",
        json={
            "vehicle_id": due_maintenance.vehicle_id,
            "maintenance_id": due_maintenance.id,
            "alert_message": "Duplicate pending alert",
            "alert_type": "Upcoming Maintenance",
            "alert_status": "Pending",
        },
    )
    assert duplicate_response.status_code == 409

    _clear_alerts_for_maintenance(db, due_maintenance.id)


def test_completed_maintenance_does_not_generate_new_alerts(db: Session, completed_maintenance: Maintenance):
    _clear_alerts_for_maintenance(db, completed_maintenance.id)

    generate_due_maintenance_alerts(db)
    
    assert (
        db.query(MaintenanceAlert)
        .filter(MaintenanceAlert.maintenance_id == completed_maintenance.id)
        .count()
        == 0
    )


def test_maintenance_report_api_matches_service(client: TestClient, db: Session, due_maintenance: Maintenance, completed_maintenance: Maintenance):
    response = client.get("/reports/maintenance")
    assert response.status_code == 200

    expected = maintenance_service.get_maintenance_report(db).model_dump()
    assert response.json() == expected


def test_celery_is_configured_and_generates_alerts(db: Session, due_maintenance: Maintenance):
    assert "check-maintenance-schedules" in celery_app.conf.beat_schedule

    db.query(MaintenanceAlert).filter(MaintenanceAlert.maintenance_id == due_maintenance.id).delete()
    db.commit()

    result = check_due_maintenance_alerts.apply()
    assert result.successful()
    assert isinstance(result.get(), int)

    created_alert = db.query(MaintenanceAlert).filter(MaintenanceAlert.maintenance_id == due_maintenance.id).first()
    assert created_alert is not None
    assert created_alert.alert_status == MaintenanceAlertStatus.PENDING

    duplicate_count = generate_due_maintenance_alerts(db)
    assert duplicate_count == 0
