import enum
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class RoleName(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    RECEPCIONISTA = "recepcionista"
    ASESOR_VEHICULOS = "asesor_vehiculos"
    TECNICO_CONSULTA = "tecnico_consulta"
    CLIENTE = "cliente"
    SISTEMA = "sistema"


user_roles = Table(
    "user_roles", Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[RoleName] = mapped_column(Enum(RoleName), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(180), nullable=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    roles: Mapped[list[Role]] = relationship(secondary=user_roles, lazy="selectin")


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
