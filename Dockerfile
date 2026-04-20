# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.14-slim AS builder
WORKDIR /build

# Compile-time deps only — do not propagate to the runtime stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.14-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    TZ=America/Argentina/Buenos_Aires

# Runtime libs only (libpq5, curl for healthcheck, tzdata for TZ)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=appuser:appuser app/ ./app/

RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# IMPORTANT: Gunicorn (not `uvicorn --workers`) — on Python 3.14 the default
# multiprocessing start method is `forkserver`, which breaks uvicorn's workers.
# Gunicorn uses os.fork() directly and sidesteps the issue.
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--log-level", "info", \
     "--forwarded-allow-ips=*"]
