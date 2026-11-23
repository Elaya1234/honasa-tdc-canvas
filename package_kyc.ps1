# =====================================================================
# Package HONASA KYC Calling & AudioCRM Suite into a Portable ZIP
# =====================================================================
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$src = Join-Path $scriptDir "honasa_audiocrm"
$targetDir = Join-Path $scriptDir "KYC_Calling_Suite"
$zipFile = Join-Path $scriptDir "KYC_Calling_Suite.zip"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   PACKAGING HONASA KYC CALLING SUITE FOR SHARING" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path $targetDir) {
    Remove-Item -Recurse -Force $targetDir
}
if (Test-Path $zipFile) {
    Remove-Item -Force $zipFile
}

Write-Host "[1/3] Assembling clean package files..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $targetDir | Out-Null

# Core server & configuration
Copy-Item (Join-Path $src "server.js") $targetDir
Copy-Item (Join-Path $src "meetings_engine.js") $targetDir -ErrorAction SilentlyContinue
Copy-Item (Join-Path $src "generate_samples.js") $targetDir -ErrorAction SilentlyContinue
Copy-Item (Join-Path $src "package.json") $targetDir
Copy-Item (Join-Path $src "package-lock.json") $targetDir
Copy-Item (Join-Path $src ".env") $targetDir -ErrorAction SilentlyContinue

# Launchers and documentation
Copy-Item (Join-Path $src "Start_KYC_Calling.bat") $targetDir -ErrorAction SilentlyContinue
Copy-Item (Join-Path $src "HOW_TO_RUN_ON_ANOTHER_LAPTOP.txt") $targetDir -ErrorAction SilentlyContinue

# Assets & web interface
Copy-Item (Join-Path $src "public") $targetDir -Recurse
Copy-Item (Join-Path $src "data") $targetDir -Recurse
Copy-Item (Join-Path $src "samples") $targetDir -Recurse
Copy-Item (Join-Path $src "node_modules") $targetDir -Recurse

# Ensure uploads directory structure exists
New-Item -ItemType Directory -Path (Join-Path $targetDir "uploads\audio") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $targetDir "exports") -Force | Out-Null

Write-Host "[2/3] Compressing into standalone KYC_Calling_Suite.zip..." -ForegroundColor Yellow
Compress-Archive -Path $targetDir -DestinationPath $zipFile -CompressionLevel Optimal

Write-Host "[3/3] Cleaning up temporary staging directory..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $targetDir

$zipSize = (Get-Item $zipFile).Length / 1MB
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host ("[SUCCESS] Portable Package Created: KYC_Calling_Suite.zip ({0:N1} MB)" -f $zipSize) -ForegroundColor Green
Write-Host ("Location: " + $zipFile) -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host ""
Write-Host "How to share with another laptop:" -ForegroundColor White
Write-Host " 1. Send 'KYC_Calling_Suite.zip' via Google Drive, Pendrive, Email, or Slack." -ForegroundColor White
Write-Host " 2. On the other laptop, extract the ZIP file." -ForegroundColor White
Write-Host " 3. Double-click 'Start_KYC_Calling.bat' to run immediately!" -ForegroundColor White
Write-Host ""
