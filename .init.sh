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
: "${DEFAULT_IMAGE:=/static/img/default_election_clean_dark.svg}"
: "${FLASK_ENV:=production}"

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

# Example: switch to Postgres
# DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/elections
EOF

echo "Wrote $ENV_FILE"

# Helpful reminders
echo ""
echo "Next steps:"
echo "  1) pip install -r requirements.txt"
echo "  2) source .env   # or your process manager will load it"
echo "  3) python run.py"
