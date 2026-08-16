# Production image for the SafetyMAIN FastAPI backend.
#
# Build context: repository root.
#   docker build -f infrastructure/production/backend.Dockerfile .
#
# The image contains application code and Alembic migrations only.
# Runtime configuration (DATABASE_URL, JWT secret, ...) is injected as
# environment variables at container start; no .env file is baked in.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependency layer: only project metadata and the package source are needed.
COPY pyproject.toml ./
COPY backend ./backend
RUN pip install --no-cache-dir .

# Migration chain and operational scripts.
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts

RUN useradd --create-home --uid 10001 safetymain \
    && chown -R safetymain:safetymain /app
USER safetymain

EXPOSE 8000

# `create_app` is a factory; the module must not connect to PostgreSQL on import.
# --proxy-headers keeps client IP/scheme accurate behind the host reverse proxy.
CMD ["uvicorn", "backend.api.app:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
