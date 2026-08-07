from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.utils.security import has_role
from app.utils.audit_log import log_action

router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user = Depends(has_role(["Admin"]))):
    return db.query(User).all()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db), current_user = Depends(has_role(["Admin"]))):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # check email unique if changing email
    if db_user.email != user_data.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
            
    db_user.name = user_data.name
    db_user.email = user_data.email
    db_user.role = user_data.role
    db.commit()
    db.refresh(db_user)
    log_action(db, action="UPDATE", resource="User", resource_id=db_user.id, details=f"Updated user {db_user.email} (Name: {db_user.name}, Role: {db_user.role})", user=current_user)
    return db_user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(has_role(["Admin"]))):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
        
    user_email_deleted = db_user.email
    db.delete(db_user)
    db.commit()
    log_action(db, action="DELETE", resource="User", resource_id=user_id, details=f"Deleted user with email {user_email_deleted}", user=current_user)
    return {"message": "User deleted successfully"}

