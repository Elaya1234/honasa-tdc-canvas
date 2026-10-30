@echo off
title Elaya Narayanan — Discussion Intelligence & AudioSuite (http://localhost:8510)
color 0B

echo ======================================================================
echo    ELAYA NARAYANAN — DISCUSSION INTELLIGENCE & AUDIOCRM SUITE
echo    Non-Blocking Background Worker Queue & Real-Time Gemini AI
echo    Local URL: http://localhost:8510
echo    Live Web:  https://elaya1234.github.io/honasa-tdc-canvas/
echo ======================================================================
echo.

set "APP_DIR=%~dp0honasa_audiocrm"

cd /d "%APP_DIR%"

:: Check if the server is already active on port 8510
netstat -ano | findstr 8510 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [INFO] AudioCRM Server is already running on http://localhost:8510.
    echo [INFO] Opening web app in your default browser...
    start http://localhost:8510
    ping 127.0.0.1 -n 3 >nul
    exit
)

echo [INFO] Starting HONASA Dynamic AudioCRM & Insights Engine...
echo [INFO] Server Port: 8510
echo [INFO] Launching background workers and Gemini engine...
echo [NOTE] Keep this window open or minimized while using the CRM.
echo ======================================================================
echo.

:: Launch Node server in background and open browser
start "" http://localhost:8510
node server.js

pause
