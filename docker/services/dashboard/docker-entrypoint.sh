#!/bin/sh
# Regenerates runtime-config.js from the API_BASE_URL env var every time the
# container starts, so the same built image works against any API host
# without a rebuild. Defaults to http://localhost:8800, matching the
# docker-compose.yml default for a single-machine deployment.
set -e

API_BASE_URL="${API_BASE_URL:-http://localhost:8800}"

cat > /app/dist/runtime-config.js <<EOF
window.__RUNTIME_CONFIG__ = {
  API_BASE_URL: "${API_BASE_URL}"
};
EOF

exec "$@"
