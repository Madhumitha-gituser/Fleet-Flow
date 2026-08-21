#!/bin/sh
set -e

# Backend container entrypoint.
# Celery worker/beat reuse this image but override CMD and leave
# RUN_MIGRATIONS unset so they do not race Alembic.

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
  echo "Alembic migrations complete."
fi

exec "$@"
