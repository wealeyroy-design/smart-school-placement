#requires -Version 5.1
<#
  Smart School Placement - launcher that works on any Windows computer.

  1. Checks the bundled Python environment (.venv) works on THIS computer.
     Virtual environments are tied to the Python install they were created
     with, so one copied from another computer usually doesn't. If it
     doesn't work, a fresh one is created with this computer's Python and
     the backend packages are installed (first run only; needs internet).
  2. Checks Node.js is installed and the frontend packages are present.
  3. Runs scripts\start.ps1, which applies migrations, starts both servers
     and opens the app in the browser.
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

function Fail([string]$msg) {
    Write-Host ""
    Write-Host "  PROBLEM: $msg" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Test-VenvWorks {
    if (-not (Test-Path $venvPython)) { return $false }
    try {
        $out = & $venvPython -c "import django, rest_framework, rest_framework_simplejwt, corsheaders; print('ok')" 2>$null
        return ($LASTEXITCODE -eq 0 -and "$out".Trim() -eq "ok")
    } catch { return $false }
}

function Find-SystemPython {
    # Returns a command (array) that runs a real Python 3.10+ on this computer, or $null.
    $candidates = @(@("py", "-3.12"), @("py", "-3"), @("python"), @("python3"))
    foreach ($c in $candidates) {
        if (-not (Get-Command $c[0] -ErrorAction SilentlyContinue)) { continue }
        try {
            $args_ = @()
            if ($c.Count -gt 1) { $args_ = $c[1..($c.Count - 1)] }
            $ok = & $c[0] @args_ -c "import sys; print(sys.version_info >= (3, 10))" 2>$null
            if ($LASTEXITCODE -eq 0 -and "$ok".Trim() -eq "True") { return ,$c }
        } catch { }
    }
    return $null
}

Write-Host ""
Write-Host "  Smart School Placement - checking this computer" -ForegroundColor Green

# ---- Python environment ----
if (Test-VenvWorks) {
    Write-Host "  Python environment: OK"
} else {
    Write-Host "  Python environment from another computer doesn't work here - setting up a new one (first run only)..." -ForegroundColor Yellow
    $py = Find-SystemPython
    if (-not $py) {
        Fail "Python 3.10 or newer is not installed. Install Python 3.12 from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then double-click the launcher again."
    }
    if (Test-Path $venv) {
        $old = Join-Path $root (".venv-old-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
        Rename-Item -Path $venv -NewName (Split-Path $old -Leaf)
        Write-Host "  (kept the old environment as $(Split-Path $old -Leaf); you can delete it)"
    }
    $pyArgs = @()
    if ($py.Count -gt 1) { $pyArgs = $py[1..($py.Count - 1)] }
    & $py[0] @pyArgs -m venv $venv
    if ($LASTEXITCODE -ne 0) { Fail "Could not create the Python environment." }
    Write-Host "  Installing backend packages (Django etc.) - this needs internet and takes a few minutes..."
    & $venvPython -m pip install --disable-pip-version-check -q -r (Join-Path $backend "requirements.txt")
    if ($LASTEXITCODE -ne 0) { Fail "Installing the backend packages failed. Check your internet connection and try again." }
    if (-not (Test-VenvWorks)) { Fail "The new Python environment still doesn't work." }
    Write-Host "  Python environment: ready" -ForegroundColor Green
}

# ---- Node.js / frontend ----
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) { $npm = (Get-Command npm -ErrorAction SilentlyContinue).Source }
if (-not $npm) {
    Fail "Node.js is not installed. Install the LTS version from https://nodejs.org/, then double-click the launcher again."
}
if (-not (Test-Path (Join-Path $frontend "node_modules\.bin\vite.cmd"))) {
    Write-Host "  Installing frontend packages - this needs internet and takes a few minutes..."
    Push-Location $frontend
    try { & $npm install --no-audit --no-fund } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { Fail "Installing the frontend packages failed. Check your internet connection and try again." }
}
Write-Host "  Node.js and frontend packages: OK"

# ---- start ----
& (Join-Path $PSScriptRoot "start.ps1")
