#!/usr/bin/env bash
# .init.sh — create or refresh a starter .env for the Flask election app
set -euo pipefail

ENV_FILE=".env"

# Generate a random SECRET_KEY (64 hex chars)
SECRET_KEY="$(python - <<'PY'
import secrets; print(secrets.token_hex(32))
PY
)"

# Sensible defaults
: "${DATABASE_URL:=sqlite:///elections.db}"
# IMPORTANT: default image is a *static filename*, no leading /static
: "${DEFAULT_IMAGE:=img/default_election_clean_dark.svg}"
: "${FLASK_ENV:=production}"
# LOCAL default: /static ; set to /vote/static in production (systemd env)
: "${STATIC_URL_PATH:=/static}"

if [[ -f "$ENV_FILE" ]]; then
  cp "$ENV_FILE" "${ENV_FILE}.bak"
  echo "Backed up existing $ENV_FILE -> ${ENV_FILE}.bak"
fi

cat > "$ENV_FILE" <<EOF
# --- Flask election app environment ---
# Change as needed. Values were generated/filled by .init.sh

SECRET_KEY=${SECRET_KEY}
DATABASE_URL=${DATABASE_URL}
DEFAULT_IMAGE=${DEFAULT_IMAGE}
FLASK_ENV=${FLASK_ENV}
STATIC_URL_PATH=${STATIC_URL_PATH}

# Example: switch to Postgres
# DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/elections

# Production hint (set via systemd drop-in instead of here):
# STATIC_URL_PATH=/vote/static
# BUILD_REV=\$(git -C /srv/simple-voting rev-parse --short HEAD)
EOF

echo "Wrote $ENV_FILE"

echo ""
echo "Next steps:"
echo "  1) pip install -r requirements.txt"
echo "  2) source .env   # or your process manager will load it"
echo "  3) python run.py"
