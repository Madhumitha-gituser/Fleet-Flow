from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse
from app.utils.security import has_role

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action (e.g., CREATE, UPDATE, DELETE, LOGIN, REGISTER)"),
    resource: Optional[str] = Query(None, description="Filter by resource (e.g., Vehicle, Driver, Shipment, Trip, user)"),
    db: Session = Depends(get_db),
    current_user=Depends(has_role(["Admin", "Fleet Manager"]))
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource:
        query = query.filter(AuditLog.resource.ilike(resource))
    
    return query.order_by(AuditLog.timestamp.desc()).all()
