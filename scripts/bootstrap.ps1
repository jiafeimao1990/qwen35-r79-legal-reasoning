param(
  [string]$ModelDir = ""
)

$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
if (-not $ModelDir) {
  $projectRoot = Split-Path -Parent $PSScriptRoot
  $ModelDir = Join-Path $projectRoot 'models\qwen3.5-9b-fp8-1949-1978-r79'
}
python -m pip install -e .
$env:R79_MODEL_DIR = $ModelDir
python -B -X utf8 -m r79_legal_reasoning download-model --destination $ModelDir
$resolvedModel = (Resolve-Path -LiteralPath $ModelDir).Path
$wslModel = (& wsl.exe wslpath -a $resolvedModel).Trim()
Write-Host "Model downloaded. In WSL run:"
Write-Host "  export R79_MODEL_DIR='$wslModel'"
Write-Host "  bash scripts/start_backend.sh"
Write-Host "Then run scripts/start_api.ps1 in PowerShell."

