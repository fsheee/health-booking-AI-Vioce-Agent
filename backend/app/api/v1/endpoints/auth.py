from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.core.dependencies import get_current_user, get_session
from app.core.security import create_access_token
from app.models.doctor import Doctor
from app.models.organization import Organization
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/signup", response_model=TokenResponse)
def signup(data: SignupRequest, session: Session = Depends(get_session)):
    org = session.exec(select(Organization).where(Organization.slug == data.org_slug)).first()
    if not org:
        org = Organization(name=data.org_slug, slug=data.org_slug)
        session.add(org)
        session.commit()
        session.refresh(org)

    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        org_id=org.id,
        hashed_password=pwd_context.hash(data.password),
        email=data.email,
        full_name=data.full_name,
        role=UserRole(data.role.value),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    if user.role == UserRole.patient:
        parts = data.full_name.strip().split(" ", 1)
        first_name = parts[0] if parts else data.full_name
        last_name = parts[1] if len(parts) > 1 else ""
        patient = Patient(
            user_id=user.id,
            org_id=org.id,
            first_name=first_name,
            last_name=last_name,
            email=data.email,
        )
        session.add(patient)
        session.commit()
    elif user.role == UserRole.doctor:
        doctor = Doctor(
            user_id=user.id,
            org_id=org.id,
            specialization=data.specialization or "",
            license_number=data.license_number or "",
        )
        session.add(doctor)
        session.commit()

    access_token = create_access_token(
        sub=str(user.id), email=user.email, role=user.role.value, org_id=str(user.org_id)
    )
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not pwd_context.verify(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if data.role and user.role.value != data.role:
        raise HTTPException(
            status_code=403,
            detail=(
                f"This account is registered as {user.role.value.replace('_', ' ')}, "
                f"not {data.role.replace('_', ' ')}"
            ),
        )

    access_token = create_access_token(
        sub=str(user.id), email=user.email, role=user.role.value, org_id=str(user.org_id)
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def me(payload: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(payload["sub"]),
        email=payload["email"],
        full_name=payload["full_name"],
        role=payload["role"],
        org_id=str(payload["org_id"]),
    )
