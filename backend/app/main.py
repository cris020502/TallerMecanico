from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .database import Base, engine, get_db
from .models import RefreshSession, Role, RoleName, User
from .schemas import (LoginRequest, RecoveryRequest, RefreshRequest, RegisterRequest,
                      ResetPasswordRequest, RoleAssignment, SessionResponse, TokenResponse, UserResponse)
from .security import create_token, decode_token, get_current_user, hash_password, require_roles, settings, verify_password

app = FastAPI(title="Taller Mecánico - Identidad", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ROLE_DESCRIPTIONS = {
    RoleName.ADMINISTRADOR: "Administración total del taller y sus catálogos.",
    RoleName.RECEPCIONISTA: "Registro de clientes, vehículos y órdenes.",
    RoleName.ASESOR_VEHICULOS: "Seguimiento y autorización de reparaciones.",
    RoleName.TECNICO_CONSULTA: "Consulta de órdenes y diagnósticos asignados.",
    RoleName.CLIENTE: "Consulta del estado de sus propios vehículos y órdenes.",
    RoleName.SISTEMA: "Cuenta de integración entre servicios.",
}


def serialize_user(user: User) -> UserResponse:
    return UserResponse(id=user.id, full_name=user.full_name, email=user.email, is_active=user.is_active, roles=[role.name for role in user.roles])


def issue_tokens(user: User, db: Session) -> TokenResponse:
    access, _ = create_token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes))
    refresh, token_id = create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_days))
    db.add(RefreshSession(user_id=user.id, token_id=token_id, expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh, user=serialize_user(user))


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        for role_name, description in ROLE_DESCRIPTIONS.items():
            if not db.scalar(select(Role).where(Role.name == role_name)):
                db.add(Role(name=role_name, description=description))
        db.commit()
        if not db.scalar(select(User).where(User.email == settings.bootstrap_admin_email.lower())):
            admin_role = db.scalar(select(Role).where(Role.name == RoleName.ADMINISTRADOR))
            db.add(User(full_name="Administrador del Taller", email=settings.bootstrap_admin_email.lower(), password_hash=hash_password(settings.bootstrap_admin_password), roles=[admin_role]))
            db.commit()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    client_role = db.scalar(select(Role).where(Role.name == RoleName.CLIENTE))
    user = User(full_name=payload.full_name.strip(), email=email, password_hash=hash_password(payload.password), roles=[client_role])
    db.add(user); db.commit(); db.refresh(user)
    return issue_tokens(user, db)


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return issue_tokens(user, db)


@app.post("/api/auth/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token = decode_token(payload.refresh_token, "refresh")
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_id == token["jti"], RefreshSession.revoked_at.is_(None)))
    if not session or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Sesión vencida")
    session.revoked_at = datetime.now(timezone.utc); db.commit()
    user = db.get(User, int(token["sub"]))
    return issue_tokens(user, db)


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token = decode_token(payload.refresh_token, "refresh")
    session = db.scalar(select(RefreshSession).where(RefreshSession.token_id == token["jti"]))
    if session and not session.revoked_at:
        session.revoked_at = datetime.now(timezone.utc); db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return serialize_user(user)


@app.get("/api/auth/sessions", response_model=list[SessionResponse])
def sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))).all()


@app.post("/api/auth/recovery")
def recovery(payload: RecoveryRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    # Siempre se responde igual: evita revelar qué correos existen.
    if user:
        token, _ = create_token(str(user.id), "recovery", timedelta(minutes=15))
        # Sustituir este registro por el proveedor de correo en producción.
        print(f"RECOVERY TOKEN para {user.email}: {token}")
    return {"message": "Si el correo existe, recibirás instrucciones para recuperar tu cuenta."}


@app.post("/api/auth/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token = decode_token(payload.token, "recovery")
    user = db.get(User, int(token["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.password_hash = hash_password(payload.new_password)
    for session in db.scalars(select(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))):
        session.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/users", response_model=list[UserResponse])
def list_users(_: User = Depends(require_roles(RoleName.ADMINISTRADOR.value)), db: Session = Depends(get_db)):
    return [serialize_user(user) for user in db.scalars(select(User)).all()]


@app.post("/api/users/{user_id}/roles", response_model=UserResponse)
def assign_role(user_id: int, payload: RoleAssignment, _: User = Depends(require_roles(RoleName.ADMINISTRADOR.value)), db: Session = Depends(get_db)):
    user, role = db.get(User, user_id), db.scalar(select(Role).where(Role.name == payload.role))
    if not user or not role:
        raise HTTPException(status_code=404, detail="Usuario o rol no encontrado")
    if role not in user.roles:
        user.roles.append(role); db.commit(); db.refresh(user)
    return serialize_user(user)
