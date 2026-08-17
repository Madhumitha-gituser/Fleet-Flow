# ---------------------------------------------------------------------------
# FleetFlow — Backend Dockerfile
# ---------------------------------------------------------------------------
# Uses Python 3.12-slim (matches psycopg2-binary and other binary wheels).
# Secrets are never baked in; all configuration is injected through
# environment variables at runtime.
# ---------------------------------------------------------------------------

FROM python:3.12-slim

# ---------- OS-level dependencies needed by psycopg2-binary ----------------
# libpq-dev is NOT required for the binary wheel but some OS stubs are.
# We keep the layer small by cleaning apt caches.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ---------- Working directory -----------------------------------------------
WORKDIR /app

# ---------- Python dependencies ---------------------------------------------
# Copy requirements first so Docker can cache this layer when source changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Application source ----------------------------------------------
# Copy the entire backend directory content into /app
COPY . .

# ---------- Runtime configuration ------------------------------------------
# DATABASE_URL, JWT_SECRET_KEY, ORS_API_KEY, CORS_ALLOWED_ORIGINS, CELERY_*
# and all other secrets are provided via docker-compose environment or a
# runtime secret manager. Do NOT hardcode values here.

# Uvicorn listens on all interfaces inside the container.
ENV HOST=0.0.0.0
ENV PORT=8000

# ---------- Port exposure ---------------------------------------------------
EXPOSE 8000

# ---------- Entrypoint ------------------------------------------------------
# app.main:app  — matches the existing FastAPI application object in app/main.py
# --host / --port read from ENV so they can be overridden without rebuilding.
CMD ["sh", "-c", "uvicorn app.main:app --host $HOST --port $PORT"]
