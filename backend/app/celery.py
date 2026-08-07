import os

from celery import Celery

from app.database import SessionLocal
from app.services.maintenance_alert_service import generate_due_maintenance_alerts


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "memory://")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "cache+memory://")
MAINTENANCE_ALERT_REMINDER_DAYS = int(os.getenv("MAINTENANCE_ALERT_REMINDER_DAYS", "7"))
MAINTENANCE_ALERT_CHECK_INTERVAL_MINUTES = int(os.getenv("MAINTENANCE_ALERT_CHECK_INTERVAL_MINUTES", "60"))

celery_app = Celery(
    "fleetflow",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.celery"],
)

celery_app.conf.update(
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true",
    task_eager_propagates=True,
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "check-maintenance-schedules": {
        "task": "app.celery.check_due_maintenance_alerts",
        "schedule": MAINTENANCE_ALERT_CHECK_INTERVAL_MINUTES * 60,
    }
}


@celery_app.task(name="app.celery.check_due_maintenance_alerts")
def check_due_maintenance_alerts() -> int:
    db = SessionLocal()
    try:
        return generate_due_maintenance_alerts(db, MAINTENANCE_ALERT_REMINDER_DAYS)
    finally:
        db.close()