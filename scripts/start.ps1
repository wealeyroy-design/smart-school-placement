#requires -Version 5.1
<#
  Smart School Placement - one-click launcher (Windows)

  Starts the Django API (SQLite) and the Vite frontend, waits for both to
  answer, then opens the app in the default browser.

  Usage:  powershell -ExecutionPolicy Bypass -File scripts\start.ps1
#>

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) { $npm = (Get-Command npm -ErrorAction SilentlyContinue).Source }

function Stop-PortOwner([int]$port) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        Write-Host "  freeing port $port (PID $($c.OwningProcess))"
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

function Wait-Port([int]$port, [int]$seconds = 45) {
    for ($i = 0; $i -lt $seconds * 2; $i++) {
        $client = New-Object System.Net.Sockets.TcpClient
        try {
            $client.Connect("127.0.0.1", $port)
            $client.Close()
            return $true
        } catch {
            Start-Sleep -Milliseconds 500
        } finally {
            $client.Close()
        }
    }
    return $false
}

Write-Host ""
Write-Host "  Smart School Placement - starting servers" -ForegroundColor Green
Write-Host ""

if (-not (Test-Path $venvPython)) {
    Write-Host "  ERROR: virtual environment not found at $venvPython" -ForegroundColor Red
    Write-Host "  Run: python -m venv .venv ; .venv\Scripts\pip.exe install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Stop-PortOwner 8000
Stop-PortOwner 5173
Start-Sleep -Seconds 1

# --- backend (SQLite so no Postgres install is needed) ---
$env:DB_ENGINE = "sqlite"
Write-Host "  applying database migrations ..."
& $venvPython (Join-Path $backend "manage.py") migrate --noinput | Out-Null
Write-Host "  starting API on http://127.0.0.1:8000 ..."
Start-Process -FilePath $venvPython `
    -ArgumentList "manage.py", "runserver", "127.0.0.1:8000", "--noreload" `
    -WorkingDirectory $backend `
    -WindowStyle Minimized

# --- frontend ---
if ($npm) {
    Write-Host "  starting UI on http://localhost:5173 ..."
    Start-Process -FilePath $npm `
        -ArgumentList "run", "dev" `
        -WorkingDirectory $frontend `
        -WindowStyle Minimized
} else {
    Write-Host "  ERROR: npm was not found on PATH" -ForegroundColor Red
    exit 1
}

$apiUp = Wait-Port 8000
$uiUp = Wait-Port 5173

Write-Host ""
if ($apiUp -and $uiUp) {
    Write-Host "  All set." -ForegroundColor Green
    Write-Host "  App   : http://localhost:5173"
    Write-Host "  API   : http://127.0.0.1:8000/api/"
    Write-Host "  Admin : http://127.0.0.1:8000/admin/  (ministry_admin / demo-pass-1234)"
    Start-Process "http://localhost:5173"
} else {
    if (-not $apiUp) { Write-Host "  WARNING: API did not start - check the API window for the error." -ForegroundColor Yellow }
    if (-not $uiUp) { Write-Host "  WARNING: UI did not start - check the UI window for the error." -ForegroundColor Yellow }
}
Write-Host ""
