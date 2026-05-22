# Deployment — LeaseIQ AI

## Docker Compose (recommended for staging)

```bash
cp backend/.env backend/.env.local
# Edit backend/.env — set SECRET_KEY (≥32 chars) and OPENAI_API_KEY
docker compose up --build -d
docker compose exec backend python seed_data.py
```

Services started:

| Service | Port | Purpose |
|---|---|---|
| `frontend` | 5173 | Vite preview |
| `backend`  | 8000 | FastAPI |
| `postgres` | 5432 | Application database |
| `redis`    | 6379 | Reserved for future Celery + cache layer |

> Note: in Docker the backend binds to `:8000`; in local dev it binds to `:8022`. Update `VITE_API_URL` accordingly.

## Manual deploy

### Backend

```bash
cd backend && pip install -r requirements.txt
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8022
```

Recommended environment in production:

```
SECRET_KEY=<64+ hex chars>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/leaseiq
ALLOWED_ORIGINS=["https://app.yourdomain.com"]
OPENAI_API_KEY=sk-...
RATE_LIMIT_PER_MINUTE=60
```

### Frontend

```bash
cd frontend && npm ci && npm run build
# Serve dist/ behind nginx or any static host; set VITE_API_URL at build time.
```

## Health checks

- `GET /health` — liveness
- `GET /ready` — readiness, pings DB and reports AI config

Both return HTTP 200 with a JSON status object.

## Production hardening checklist

- [ ] Change all default user passwords after first seed
- [ ] Rotate `SECRET_KEY` if it was committed anywhere
- [ ] Set `ALLOWED_ORIGINS` to your production domain only
- [ ] Terminate TLS at the reverse proxy
- [ ] Configure log aggregation against the `X-Request-ID` field
- [ ] Set up `pg_dump` + offsite backups with a documented RPO
- [ ] Enable Sentry (or equivalent) via `SENTRY_DSN` — _roadmap_
