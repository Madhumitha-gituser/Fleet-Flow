from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_email: Optional[str]
    action: str
    resource: str
    resource_id: Optional[str]
    details: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
