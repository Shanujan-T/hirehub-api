#!/usr/bin/env bash
set -euo pipefail

# Nixpacks/Railway virtualenv paths
if [ -d "/opt/venv/bin" ]; then
  export PATH="/opt/venv/bin:${PATH}"
fi
export PATH="${HOME}/.local/bin:${PATH}"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Python not found in PATH"
  exit 1
fi

echo "Using Python: $($PYTHON --version)"

$PYTHON migrate_schema.py || echo "Migration skipped"

exec $PYTHON -m gunicorn wsgi:app \
  --bind "0.0.0.0:${PORT:-5000}" \
  --workers 1 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
