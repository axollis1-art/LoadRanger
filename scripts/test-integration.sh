#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null; then
  echo "Docker is required for PostgreSQL integration tests. Rebuild the devcontainer with Docker access."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "The Docker daemon is unavailable. Start Docker or rebuild the devcontainer with Docker access."
  exit 1
fi

docker compose up --detach --wait db
database_host=localhost
if getent hosts host.docker.internal >/dev/null 2>&1; then
  database_host=host.docker.internal
fi
export LOADRANGER_DATABASE_URL="postgresql+psycopg://loadranger:loadranger@${database_host}:5432/loadranger"
uv run pytest -m integration
