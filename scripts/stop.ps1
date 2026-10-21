#requires -Version 5.1
<#
  Stops the Django API and Vite frontend started by scripts\start.ps1.
  Usage:  powershell -ExecutionPolicy Bypass -File scripts\stop.ps1
#>

foreach ($port in 8000, 5173) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "  stopped port $port (PID $($c.OwningProcess))"
    }
}

Write-Host "  Servers stopped." -ForegroundColor Green
