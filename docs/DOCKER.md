# Docker Guide

## Development Compose (hot reload)

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Production-style Compose

```powershell
docker compose up --build
```

- Frontend (Nginx): `http://localhost:3000`
- Backend API (direct): `http://localhost:8000`

Frontend routes `/api/*` are proxied to backend through Nginx.