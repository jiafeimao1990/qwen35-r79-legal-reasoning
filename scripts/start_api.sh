#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export R79_WIKI_DB="${R79_WIKI_DB:-$PROJECT_ROOT/runtime/wiki.sqlite3}"
exec uvicorn r79_legal_reasoning.api:app \
  --host "${R79_API_HOST:-127.0.0.1}" \
  --port "${R79_API_PORT:-8088}"

