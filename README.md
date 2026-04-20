# afip-services-api

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.14-blue?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Status" src="https://img.shields.io/badge/status-stable-green">
</p>

> REST API FastAPI that wraps the AFIP/ARCA SOAP web services (WSAA + WSN) with JWT auth, a minimal admin dashboard and a Docker-ready multi-stage image.

## Features

- REST endpoints to query AFIP padrón e inscripción de personas.
- JWT authentication — `POST /api/v1/token` issues, everything else validates.
- `/health` at the root (no auth) for orchestrators.
- Configurable rate limiting (`slowapi`).
- Structured JSON logging (prod) / text (dev) with request-id per call.
- Dockerfile multi-stage + Gunicorn (uvicorn workers) running as non-root user.
- Minimal admin dashboard (Jinja2 + Tailwind CDN) with login + home + service health badges.
- **Dedup**: the SOAP/WSAA layer lives in the external [`afip-services`](https://github.com/GDelpo/afip-services) package (installed via pip), not copied into this repo.

## Architecture

```
afip-services-api/
├── Dockerfile              # Multi-stage Python 3.14 + gunicorn
├── docker-compose-example.yml
├── requirements.txt        # Pinned deps + afip-services @ git main
├── .env.example
└── app/
    ├── main.py             # App factory, lifespan, middleware, /health
    ├── config.py           # pydantic-settings (model_validator + computed_field)
    ├── api.py              # Single APIRouter: /token, /inscription, /padron
    ├── service.py          # Business logic (uses afip_services package)
    ├── schemas.py          # Pydantic models (camelCase aliasing)
    ├── dependencies.py     # Annotated deps (CurrentUser, InscriptionService…)
    ├── security.py         # JWT create + verify
    ├── middleware.py       # ProxyHeaders + RequestLogging
    ├── exceptions.py       # ServiceException + handlers
    ├── limiter.py          # slowapi Limiter
    ├── logger.py           # configure_logging() — JSON/text
    └── dashboard/
        ├── routes.py       # /dashboard + /dashboard/login
        ├── static/         # self-hosted assets (future)
        └── templates/      # base, shell, login, pages, _partials, _js
```

**Middleware order** (see CLAUDE.md): `ProxyHeadersMiddleware` → `RequestLoggingMiddleware` → `CORSMiddleware` → `SlowAPIMiddleware`.

## Requirements

- Python 3.14 (also runs on 3.12+).
- AFIP **certificate + private key** registered for homologación/producción.
- Docker + Docker Compose for container deploys.

## Quickstart

### Local

```bash
git clone https://github.com/GDelpo/afip-services-api.git
cd afip-services-api
python -m venv env
.\env\Scripts\Activate.ps1       # Windows
# source env/bin/activate        # Linux/macOS
pip install -r requirements.txt
cp .env.example .env             # edit cert/key paths + AUTH_* + SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/api/v1/docs>
- Health: <http://localhost:8000/health>
- Dashboard: <http://localhost:8000/dashboard>

### Docker

```bash
cp docker-compose-example.yml docker-compose.yml
# mount your credentials folder (cert/key) and edit .env
docker compose up -d --build
```

## Configuration

| Variable | Descripción |
|----------|-------------|
| `ENVIRONMENT` | `dev` / `staging` / `prod` (drives `is_production` computed_field) |
| `DEBUG` | `true` turns logging to DEBUG level |
| `LOG_FORMAT` | `json` (prod) or `text` (dev) |
| `LOGTAIL_TOKEN` | Optional — enables Logtail handler when set |
| `AUTH_USERNAME` / `AUTH_PASSWORD` | Single-user fallback |
| `AUTH_SECRET_KEY` | JWT signing key — `openssl rand -hex 32` |
| `AUTH_EXPIRES_IN` | Token TTL in minutes |
| `API_PREFIX` | Defaults to `/api/v1` |
| `CORS_ORIGINS` | JSON list |
| `CERTIFICATE_PATH` / `PRIVATE_KEY_PATH` / `PASSPHRASE` | AFIP credentials |
| `RATE_LIMIT_TIME` / `MAX_CALLS` | slowapi limit (e.g. 60 calls / 60 s) |

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET    | `/health` | no | Liveness/readiness — returns name + version + environment |
| GET    | `/dashboard` · `/dashboard/login` | cookie-less (localStorage) | Minimal admin UI |
| POST   | `/api/v1/token` | no | OAuth2 password → JWT |
| POST   | `/api/v1/inscription` | JWT | Query WS_SR_CONSTANCIA_INSCRIPCION for a list of CUITs |
| GET    | `/api/v1/inscription/health` | JWT | Ping AFIP inscription dummy |
| POST   | `/api/v1/padron` | JWT | Query WS_SR_PADRON_A13 for a list of CUITs |
| GET    | `/api/v1/padron/health` | JWT | Ping AFIP padrón dummy |

## Adding a new AFIP service

This API wraps services declared in the underlying [`afip-services`](https://github.com/GDelpo/afip-services) package (v0.2+). The catalog lives in a YAML file inside that package — `afip_services/services.yaml`.

**If the new service is padron-family** (same CUITs-in / personas-out shape):

1. Add an entry to `services.yaml` in the package repo (kind `padron_list` or `padron_single`). No Python code needed.
2. Here in the API, copy the `/padron` block in `app/api.py` and `PadronService` in `app/dependencies.py` to register a new route + injected WSN client for the service.

**If the new service has a different shape** (wsfe, wsmtx, wsfexv1, …): add the YAML entry with a custom `kind`, register a handler in the package with `@register_handler("your_kind")`, then add the route here wrapping `wsn.request(**kwargs)`.

See the package README for the full extension guide.

## Related

- [`afip-services`](https://github.com/GDelpo/afip-services) — Python package with the WSAA + SOAP logic consumed by this API.
- [`afip-services-applied`](https://github.com/GDelpo/afip-services-applied) — Example consumer of this API.

## License

[MIT](LICENSE) © 2026 Guido Delponte
