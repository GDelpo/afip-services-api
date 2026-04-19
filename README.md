# afip-services-api

<p>
  <img alt="Python" src="https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Status" src="https://img.shields.io/badge/status-stable-green">
</p>

> REST API FastAPI que expone los web services SOAP de AFIP/ARCA (WSAA + WSN) con autenticación JWT, rate limiting y deploy con Docker Compose.

## Features

- Endpoints REST para consultar padrón e inscripción de AFIP.
- Autenticación JWT — `/token` emite, el resto valida.
- Rate limiting configurable (`slowapi`).
- Logging estructurado con request ID por llamada.
- Docker Compose listo — gunicorn + uvicorn workers.
- Cache in-memory de tickets WSAA (renovación automática).

## Requirements

- Python 3.9+
- **Certificado + clave AFIP** registrados.
- Docker + Docker Compose (opcional para el deploy con una sola línea).

## Quickstart

### Install (local)

```bash
git clone https://github.com/GDelpo/afip-services-api.git
cd afip-services-api
python -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env-example .env
# Editar .env con tu cert, key, y SECRET_KEY JWT
```

### Run (local)

```bash
uvicorn main:app --reload --port 8000
```

Docs interactivos: <http://localhost:8000/docs>

### Run (Docker)

```bash
cp docker-compose-example.yml docker-compose.yml
# Editar volúmenes (cert/key) y variables del .env
docker compose up -d --build
```

## Configuration

| Variable | Descripción |
|----------|-------------|
| `AFIP_ENV` | `testing` o `production` |
| `AFIP_CERT_PATH` | Path al cert dentro del container |
| `AFIP_KEY_PATH` | Path a la key dentro del container |
| `SECRET_KEY` | Firma JWT — generar con `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | TTL del token JWT |
| `ALLOWED_USERS` | Usuarios válidos (JSON: `{"user": "hashed_pw"}`) |
| `RATE_LIMIT` | Ej. `100/minute` |

## API

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/token` | Login — devuelve JWT |
| GET  | `/padron/{cuit}` | Consulta padrón (requiere JWT) |
| GET  | `/inscription/{cuit}` | Consulta inscripción (requiere JWT) |
| GET  | `/health` | Health check |

## Architecture

```
afip-services-api/
├── main.py              # FastAPI entrypoint
├── app/
│   ├── afip_ws/         # Capa SOAP WSAA (equivalente a afip-services)
│   ├── api/             # Routers: auth, padron, inscription
│   └── core/            # Config, security, limiter, logging
├── Dockerfile
└── docker-compose-example.yml
```

**Stack:** FastAPI + Uvicorn + Gunicorn, `zeep` para SOAP, `python-jose` para JWT, `slowapi` para rate limiting.

## Relacionados

- [`afip-services`](https://github.com/GDelpo/afip-services) — cliente SOAP base standalone (incorporado dentro de este API).
- [`afip-services-applied`](https://github.com/GDelpo/afip-services-applied) — cliente consumer del API.

## License

[MIT](LICENSE) © 2026 Guido Delponte
