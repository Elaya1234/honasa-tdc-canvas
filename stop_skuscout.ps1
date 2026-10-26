$Port = 8503
Write-Host "Checking for active SKUScout server on port $Port..." -ForegroundColor Cyan

$Connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

if ($Connections) {
    $ProcessIds = $Connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($PidVal in $ProcessIds) {
        try {
            $Proc = Get-Process -Id $PidVal -ErrorAction Stop
            Write-Host "Terminating process: $($Proc.ProcessName) (PID: $PidVal)..." -ForegroundColor Yellow
            Stop-Process -Id $PidVal -Force
            Write-Host "Successfully stopped SKUScout server." -ForegroundColor Green
        } catch {
            Write-Host "Failed to kill process PID: $PidVal ($($_.Exception.Message))" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No active process found running on port $Port." -ForegroundColor Green
}
