param(
    [ValidateSet('test','serve','demo')][string]$Action = 'test',
    [int]$Port = 8000
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
# Prefer a project venv, then Codex's bundled runtime, then a working Python.
$candidates = @(
    (Join-Path $PSScriptRoot '.venv/Scripts/python.exe'),
    (Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'),
    'python', 'py'
)
$labPython = $null
foreach ($candidate in $candidates) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        try {
            & $candidate -c 'import sys; assert sys.version_info >= (3,10)' 2>$null
            if ($LASTEXITCODE -eq 0) { $labPython = $candidate; break }
        } catch { }
    }
}
if (-not $labPython) { throw 'Install Python 3.10+ and run again.' }
$env:PYTHONPATH = Join-Path $PSScriptRoot '.lab5-deps'
$env:PYTHONUTF8 = '1'
if ($Action -eq 'test') {
    & $labPython -c 'import pytest,jsonschema,yaml,coverage,openapi_spec_validator' 2>$null
    if ($LASTEXITCODE -ne 0) {
        & $labPython -m pip install --target .lab5-deps -r requirements-dev.txt
        if ($LASTEXITCODE -ne 0) { throw 'Test dependency installation failed.' }
    }
    & $labPython -X utf8 scripts/check_lab5.py
} elseif ($Action -eq 'serve') {
    & $labPython -X utf8 -m src.api --port $Port
} else {
    & $labPython -X utf8 scripts/demo_lab5.py
}
exit $LASTEXITCODE
