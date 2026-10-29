#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="${R79_MODEL_DIR:-$HOME/.cache/r79-legal-reasoning/model}"
PORT="${R79_BACKEND_PORT:-8000}"

test -f "$MODEL_DIR/config.json" || {
  echo "Model not found at $MODEL_DIR. Run: r79-legal download-model" >&2
  exit 2
}

exec vllm serve "$MODEL_DIR" \
  --host 127.0.0.1 --port "$PORT" \
  --dtype float16 \
  --language-model-only \
  --max-model-len 16384 \
  --speculative-config '{"method":"mtp","num_speculative_tokens":3}' \
  --enable-lora --lora-dtype float16 \
  --max-loras 3 --max-cpu-loras 3 --max-lora-rank 16 \
  --lora-modules \
    facts_1949="$MODEL_DIR/adapters/1949" \
    procedure_1978="$MODEL_DIR/adapters/1978" \
    candidate_r79="$MODEL_DIR/adapters/r79"

