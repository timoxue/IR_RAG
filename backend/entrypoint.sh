#!/usr/bin/env bash
set -euo pipefail

# Move to app dir and set Python path
cd /app
export PYTHONPATH=/app

# Migrate DB if alembic is configured
if [ -f "/app/alembic.ini" ]; then
	echo "[entrypoint] running alembic migrations..."
	alembic upgrade head || echo "[entrypoint] alembic failed (continuing)"
fi

# Start Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000