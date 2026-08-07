import logging
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger("fleetflow")

def log_action(
    db: Session,
    action: str,
    resource: str,
    resource_id: str | int | None = None,
    details: str | None = None,
    user: User | None = None,
):
    """
    Log an audit action in the database.
    This runs inside its own try-except block to prevent database transaction errors
    from breaking the main API flow.
    """
    try:
        user_id = user.id if user else None
        user_email = user.email if user else None

        db_log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details,
        )
        db.add(db_log)
        db.commit()
        logger.info(f"Audit Log: {action} on {resource} ID {resource_id} by {user_email or 'Anonymous'}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to write audit log: {e}")
