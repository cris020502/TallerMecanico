from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import User

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
settings = get_settings()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_token(subject: str, kind: str, expires: timedelta, token_id: str | None = None) -> tuple[str, str]:
    jti = token_id or str(uuid4())
    payload = {"sub": subject, "type": kind, "jti": jti, "exp": datetime.now(timezone.utc) + expires}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm), jti


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o vencido") from error
    if payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token no válido")
    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    payload = decode_token(credentials.credentials, "access")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no disponible")
    return user


def require_roles(*allowed: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if not {role.name.value for role in user.roles}.intersection(allowed):
            raise HTTPException(status_code=403, detail="No cuenta con permisos para esta operación")
        return user
    return checker
