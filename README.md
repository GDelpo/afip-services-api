# afip-services-api

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.14-blue?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.162-009688?logo=fastapi&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

> FastAPI service that exposes the AFIP/ARCA SOAP web services over REST, with JWT auth, rate limiting, a small admin dashboard and a multi-stage Docker image.

The SOAP and WSAA logic lives in the [`afip-services`](https://github.com/GDelpo/afip-services) package, installed with pip. This repo only adds the HTTP layer.

## Features

- One `POST /api/v1/<slug>` query route and one `GET /api/v1/<slug>/health` route per service in the `afip-services` catalog, registered at startup.
- JWT auth: `POST /api/v1/token` issues a token for the single configured user; every AFIP route requires it.
- `/health` at the root, without auth, for orchestrators.
- Rate limiting with `slowapi`, applied to every route.
- JSON logs (or plain text) with a request id per call; optional Logtail.
- Minimal admin dashboard (Jinja2 + Tailwind CDN): login, home and service health badges.
- Multi-stage Dockerfile, non-root user, Gunicorn with one Uvicorn worker.

## Requirements

- Python 3.14
- An AFIP digital certificate and private key, registered for the services you call.
- Docker, for the container deploy.

## Quickstart

### Local

```bash
git clone https://github.com/GDelpo/afip-services-api.git
cd afip-services-api
python -m venv env
source env/bin/activate          # Windows: .\env\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # set AUTH_*, the certificate paths and AUTH_SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/api/v1/docs>
- Health: <http://localhost:8000/health>
- Dashboard: <http://localhost:8000/dashboard>

At startup the app gets one WSAA ticket per service. A service whose client fails to start (missing certificate, AFIP down) answers `503` and the rest keep working.

### Docker

```bash
cp docker-compose-example.yml docker-compose.yml
mkdir credentials                # put the certificate and key here; .env paths point to /app/credentials/...
docker compose up -d --build
```

The image runs a single Gunicorn worker on purpose. Each worker would ask WSAA for its own ticket at startup, and WSAA refuses a new ticket while the previous one is still valid, so extra workers would come up without AFIP clients. The AFIP routes are sync and run in FastAPI's threadpool, so one worker still serves requests concurrently.

### Example call

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/token \
  -d "username=$AUTH_USERNAME" -d "password=$AUTH_PASSWORD" | jq -r .accessToken)

curl -s -X POST localhost:8000/api/v1/padron \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"personaIds": [20111111112]}'      # example CUIT
```

```json
{"data": [{"20111111112": {"datosGenerales": {"idPersona": 20111111112, "...": "..."}}}]}
```

Each requested id comes back as a string key, in request order. An id AFIP rejected or did not answer carries `{"error": "..."}` instead of data; see the [result format](https://github.com/GDelpo/afip-services#result-format) in `afip-services`. `personaIds` takes 1 to 250 integers.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `prod` | `dev`, `staging` or `prod`. Only `prod` with `DEBUG=false` uses the AFIP production endpoints; anything else uses homologación. |
| `DEBUG` | `false` | DEBUG log level. Also switches AFIP to homologación. |
| `LOG_DIR_PATH` | `logs` | Folder for the log files. |
| `LOG_FORMAT` | `json` | `json` or `text`. |
| `LOGTAIL_TOKEN` | — | Sends logs to Logtail when set. |
| `AUTH_USERNAME` / `AUTH_PASSWORD` | required | The single user allowed to get a token. |
| `AUTH_SECRET_KEY` | required | JWT signing key, at least 32 characters: `openssl rand -hex 32`. |
| `AUTH_ALGORITHM` | `HS256` | JWT algorithm. |
| `AUTH_EXPIRES_IN` | `30` | Token lifetime in minutes. |
| `API_PREFIX` | `/api/v1` | Prefix for the API routes and the docs. |
| `CORS_ORIGINS` | `[]` | JSON list of origins allowed to call the API from a browser. Empty means same-origin only, which is enough for the dashboard. |
| `CERTIFICATE_PATH` / `PRIVATE_KEY_PATH` | required | AFIP certificate and key. |
| `PASSPHRASE` | — | Private key passphrase, if any. |
| `RATE_LIMIT_TIME` / `MAX_CALLS` | `60` / `60` | `MAX_CALLS` requests per `RATE_LIMIT_TIME` seconds, per client IP. |

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | no | Name, version and environment |
| GET | `/dashboard`, `/dashboard/login` | no (the page keeps the JWT in localStorage) | Admin UI |
| POST | `/api/v1/token` | no | OAuth2 password form → JWT |
| POST | `/api/v1/inscription` | JWT | `WS_SR_CONSTANCIA_INSCRIPCION` for a list of CUITs |
| GET | `/api/v1/inscription/health` | JWT | AFIP `dummy` for that service |
| POST | `/api/v1/padron` | JWT | `WS_SR_PADRON_A13` for a list of CUITs |
| GET | `/api/v1/padron/health` | JWT | AFIP `dummy` for that service |

## Adding an AFIP service

Services come from the `afip-services` catalog (`afip_services/services.yaml`). A padron-family entry needs no code here:

```yaml
services:
  WS_SR_PADRON_A4:
    testing_service_url: https://awshomo.afip.gov.ar/...
    testing_wsdl_url:   https://awshomo.afip.gov.ar/...
    production_service_url: https://aws.afip.gov.ar/...
    production_wsdl_url:    https://aws.afip.gov.ar/...
    service_name: ws_sr_padron_a4
    method_name:  getPersona
    kind:         padron_single     # or padron_list
    slug:         padron-a4         # route path
    description:  AFIP Padrón A4
```

At startup the API registers `POST /api/v1/padron-a4` and `GET /api/v1/padron-a4/health` for it.

A service with another shape (wsfe, wsmtx, wsfexv1, …) needs a custom `kind`, a handler registered with `@register_handler("your_kind")` and its route added by hand in `app/api.py`. Auto-registration only covers the kinds in `AUTO_KINDS` (`padron_list`, `padron_single`). The [`afip-services` README](https://github.com/GDelpo/afip-services) has the package side.

## Tests

```bash
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
pytest
```

The tests use FastAPI's `TestClient` with a fake WSN client, so they need neither a certificate nor AFIP. They cover the token flow (bad credentials, invalid and expired tokens), the generated routes, the response shape, input validation, service health, the `503` when a service is down, CORS and the dashboard pages. CI also builds the Docker image.

## Architecture

```
afip-services-api/
├── Dockerfile              # multi-stage Python 3.14 + gunicorn (1 worker)
├── docker-compose-example.yml
├── requirements.txt        # pinned deps + afip-services pinned to a commit
├── requirements-dev.txt    # test and lint tools
├── pyproject.toml          # ruff and pytest config
├── app/
│   ├── main.py             # app factory, lifespan, middleware, /health
│   ├── config.py           # pydantic-settings
│   ├── api.py              # /token + routes generated from the catalog
│   ├── service.py          # builds the WSN clients and calls them
│   ├── schemas.py          # Pydantic models (camelCase JSON)
│   ├── dependencies.py     # CurrentUser, get_wsn_client
│   ├── security.py         # JWT create + verify (PyJWT)
│   ├── middleware.py       # ProxyHeaders + RequestLogging
│   ├── exceptions.py       # ServiceException + handlers
│   ├── limiter.py          # slowapi Limiter
│   ├── logger.py           # JSON / text logging
│   └── dashboard/          # /dashboard routes and templates
└── tests/                  # TestClient suite with a fake WSN
```

**Middleware order**: `ProxyHeadersMiddleware` → `RequestLoggingMiddleware` → `CORSMiddleware` → `SlowAPIMiddleware`.

## Related

- [`afip-services`](https://github.com/GDelpo/afip-services): the Python package with the WSAA and SOAP logic this API uses.

## License

[MIT](LICENSE) © 2026 Guido Delponte
