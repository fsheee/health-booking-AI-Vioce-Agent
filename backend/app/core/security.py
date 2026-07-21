from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

security_scheme = HTTPBearer()


def create_access_token(sub: str, email: str, role: str, org_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "org_id": org_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return {
            "token": token,
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "org_id": payload.get("org_id"),
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
