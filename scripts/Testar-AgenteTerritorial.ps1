param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path)
$ErrorActionPreference = "Stop"
Push-Location $RepoRoot
try {
    if (-not (Test-Path '.venv')) { py -3 -m venv .venv }
    $python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
    & $python -m pip install -r requirements-territorial.txt
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependências" }
    & $python -m pytest -v tests/test_territorial.py
    if ($LASTEXITCODE -ne 0) { throw "Testes falharam" }
    Write-Host "Testes aprovados. Para iniciar a API:"
    Write-Host '& ".\.venv\Scripts\python.exe" -m uvicorn agents.territorial.api:app --reload --port 8006'
} finally { Pop-Location }
