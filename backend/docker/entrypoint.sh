#!/bin/sh
# ==============================================================================
# FoodBridge AI - Backend Entrypoint Script
# Waits for PostgreSQL to be ready and available before launching applications.
# ==============================================================================
set -e

echo "Starting Backend Entrypoint..."

# Wait for PostgreSQL
if [ -n "$POSTGRES_SERVER" ]; then
  echo "Checking database connection on $POSTGRES_SERVER:$POSTGRES_PORT..."
  until pg_isready -h "$POSTGRES_SERVER" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER"; do
    echo "PostgreSQL is unavailable - sleeping..."
    sleep 2
  done
  echo "PostgreSQL is up and running!"
fi

# Run database migrations if we are running in the API server mode
# (This avoids running migrations multiple times concurrently in workers)
if [ "$1" = "uvicorn" ]; then
  echo "Running FastAPI Server setup tasks..."
  # alembic upgrade head || echo "Database migrations failed, proceeding anyway..."
fi

echo "Executing command: $@"
exec "$@"
