from enum import Enum

from pydantic import BaseModel, EmailStr


class SignupRole(str, Enum):
    patient = "patient"
    doctor = "doctor"
    front_desk = "front_desk"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str | None = None


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    org_slug: str
    role: SignupRole = SignupRole.patient
    specialization: str | None = None
    license_number: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    org_id: str


class ErrorResponse(BaseModel):
    detail: str
