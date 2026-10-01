# Taller Mecánico — Fase 1: Identidad

Proyecto base para identidad, usuarios, roles, registro, sesiones, autenticación, autorización y recuperación de contraseña.

## Requisitos

- Python 3.11 o superior
- Node.js 20 o superior

## Ejecutar la API (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

API y documentación: http://localhost:8000/docs

## Ejecutar la SPA (Vue + Vite)

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

Abre: http://localhost:5173

## Acceso inicial

| Usuario | Contraseña | Rol |
|---|---|---|
| admin@taller.local | Cambiar123! | Administrador del taller |

Cambia la contraseña y `SECRET_KEY` antes de publicar el sistema.
