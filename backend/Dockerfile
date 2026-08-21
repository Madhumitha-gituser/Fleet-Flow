# ---------------------------------------------------------------------------
# FleetFlow — Backend Dockerfile
# ---------------------------------------------------------------------------
# Python 3.12-slim. Secrets are injected at runtime, never baked in.
# requirements.docker.txt is the Linux production set (no Windows-only packages
# and without unused ML/Google SDKs that bloated/broke image builds).
# ---------------------------------------------------------------------------

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.docker.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.docker.txt

COPY . .

RUN sed -i 's/\r$//' /app/docker-entrypoint.sh \
    && chmod +x /app/docker-entrypoint.sh

ENV HOST=0.0.0.0
ENV PORT=8000
ENV ENVIRONMENT=production

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
