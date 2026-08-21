import os

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User

# JWT_SECRET_KEY must be set to a strong random value in production.
# The fallback is kept ONLY for local development convenience.
_jwt_secret = os.environ.get("JWT_SECRET_KEY", "").strip()
_environment = os.environ.get("ENVIRONMENT", "development").lower()
if not _jwt_secret:
    if _environment in ("production", "prod"):
        raise RuntimeError("JWT_SECRET_KEY must be set when ENVIRONMENT=production")
    _jwt_secret = "fleetflow_secret_key"

SECRET_KEY: str = _jwt_secret
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


security_scheme = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


_ROLE_ALIASES = {
    "admin": "Admin",
    "fleet manager": "Fleet Manager",
    "fleet_manager": "Fleet Manager",
    "dispatcher": "Dispatcher",
    "driver": "Driver",
}


def normalize_role(role: str | None) -> str:
    """Map stored/JWT role values to a canonical title (Admin, Fleet Manager, ...)."""
    if not role:
        return ""
    key = " ".join(str(role).strip().lower().replace("_", " ").replace("-", " ").split())
    return _ROLE_ALIASES.get(key, str(role).strip())


def has_role(allowed_roles: list):
    def dependency(current_user: User = Depends(get_current_user)):
        current = normalize_role(current_user.role).lower()
        allowed = {normalize_role(role).lower() for role in allowed_roles}
        if current not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource"
            )
        return current_user
    return dependency
