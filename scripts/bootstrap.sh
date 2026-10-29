#!/usr/bin/env bash
set -euo pipefail

python -m pip install -e .
python -m pip install -r requirements-backend.txt
python -B -X utf8 -m r79_legal_reasoning download-model
mkdir -p runtime
if [[ ! -f runtime/wiki.sqlite3 ]]; then
  python -B -X utf8 -m r79_legal_reasoning build-wiki \
    --input data/wiki_demo.jsonl \
    --output runtime/wiki.sqlite3 \
    --privacy-reviewed --rights-confirmed
fi
echo "Bootstrap complete. Start scripts/start_backend.sh and scripts/start_api.sh in separate terminals."
