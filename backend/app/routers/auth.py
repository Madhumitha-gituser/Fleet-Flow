from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import register_user, login_user
from app.utils.audit_log import log_action
from app.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Register API
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    res = register_user(user, db)
    log_action(db, action="REGISTER", resource="User", resource_id=res.id, details=f"User registered with email {res.email}", user=res)
    return res


# Login API
@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    res = login_user(user, db)
    db_user = db.query(User).filter(User.email == user.email).first()
    log_action(db, action="LOGIN", resource="User", resource_id=db_user.id, details="User logged in successfully", user=db_user)
    return res