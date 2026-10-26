$ErrorActionPreference = "SilentlyContinue"
Write-Host "Checking for Instagram Reel Collector server on port 8502..." -ForegroundColor Cyan

$connections = Get-NetTCPConnection -LocalPort 8502 -ErrorAction SilentlyContinue
if ($connections) {
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        if ($procId -gt 0) {
            try {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "Stopped process ID: $procId" -ForegroundColor Green
            } catch {}
        }
    }
    Write-Host "Instagram Reel Collector server stopped successfully." -ForegroundColor Green
} else {
    Write-Host "Instagram Reel Collector server is not currently running." -ForegroundColor Yellow
}
Start-Sleep -Seconds 2
