import uuid

from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from app.core.security import verify_token
from app.models.user import User, UserRole


def get_session() -> Session:
    from app.models.base import engine
    with Session(engine) as session:
        yield session


def get_current_user(
    payload: dict = Depends(verify_token),
    session: Session = Depends(get_session),
) -> dict:
    user = session.get(User, uuid.UUID(payload.get("sub")))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return {
        "token": payload.get("token"),
        "sub": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "org_id": user.org_id,
    }


def require_role(role: UserRole):
    def role_checker(payload: dict = Depends(get_current_user)):
        if payload.get("role") != role.value and payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return payload
    return role_checker


def require_any_role(*roles: UserRole):
    def role_checker(payload: dict = Depends(get_current_user)):
        if payload.get("role") not in [r.value for r in roles] and payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return payload
    return role_checker
