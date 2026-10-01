from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from .models import RoleName


def validate_password(value: str) -> str:
    if not (any(c.isupper() for c in value) and any(c.islower() for c in value) and any(c.isdigit() for c in value)):
        raise ValueError("La contraseña requiere mayúscula, minúscula y número")
    return value


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    _password = field_validator("password")(validate_password)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    roles: list[RoleName]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class RecoveryRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)
    _password = field_validator("new_password")(validate_password)


class RoleAssignment(BaseModel):
    role: RoleName


class SessionResponse(BaseModel):
    id: int
    expires_at: datetime
