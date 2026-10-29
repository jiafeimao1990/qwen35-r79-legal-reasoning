$ErrorActionPreference = 'Stop'
if (-not $env:R79_API_HOST) { $env:R79_API_HOST = '127.0.0.1' }
if (-not $env:R79_API_PORT) { $env:R79_API_PORT = '8088' }
if (-not $env:R79_WIKI_DB) {
  $projectRoot = Split-Path -Parent $PSScriptRoot
  $env:R79_WIKI_DB = Join-Path $projectRoot 'runtime\wiki.sqlite3'
}
python -m uvicorn r79_legal_reasoning.api:app --host $env:R79_API_HOST --port $env:R79_API_PORT

