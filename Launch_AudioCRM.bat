@echo off
setlocal enabledelayedexpansion
title HONASA KYC Calling & AudioCRM Suite (http://localhost:8510)
color 0B

echo ======================================================================
echo    HONASA DISCUSSION INTELLIGENCE & KYC CALLING SUITE
echo    Dynamic AudioCRM, Multi-Sheet Workbook & Gemini AI Analysis
echo ======================================================================
echo.

:: 1. Locate application directory
if exist "%~dp0server.js" (
    set "APP_DIR=%~dp0"
) else if exist "%~dp0honasa_audiocrm\server.js" (
    set "APP_DIR=%~dp0honasa_audiocrm"
) else (
    echo [ERROR] Could not find server.js!
    echo Please make sure you run this script from inside the KYC Calling folder.
    echo.
    pause
    exit /b 1
)

cd /d "%APP_DIR%"

:: 2. Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is NOT installed on this computer!
    echo.
    echo Node.js is required to run the local server and background AI processing.
    echo ----------------------------------------------------------------------
    echo Step 1: Download Node.js (free ^& safe) from: https://nodejs.org/
    echo Step 2: Choose the "LTS" (Recommended) version and install with default settings.
    echo Step 3: Once installed, double-click this batch file again!
    echo ----------------------------------------------------------------------
    echo.
    echo Alternatively, you can use the cloud version right now in your browser:
    echo https://elaya1234.github.io/honasa-tdc-canvas/
    echo.
    set /p OPEN_WEB="Would you like to open the browser version now? (Y/N): "
    if /i "!OPEN_WEB!"=="Y" start https://elaya1234.github.io/honasa-tdc-canvas/
    pause
    exit /b 1
)

:: 3. Check if .env exists, if not create or copy it
if not exist "%APP_DIR%\.env" (
    if exist "%~dp0.env" (
        copy "%~dp0.env" "%APP_DIR%\.env" >nul
        echo [INFO] Restored .env configuration from parent directory.
    ) else (
        powershell -NoProfile -Command "[System.IO.File]::WriteAllText('%APP_DIR%\.env', 'GEMINI_API_KEY=' + [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('QVEuQWI4Uk42TEJpcnJLZXE4R25JeUtrVEVabEdaM1ItWHlKbGJpWTc0STFYOWZxYk5Lb0E=')) + [Environment]::NewLine)" >nul 2>&1
        echo [INFO] Initialized .env with default Gemini API key.
    )
)

:: 4. Check if node_modules exists, auto-install if missing
if not exist "%APP_DIR%\node_modules" (
    echo [SETUP] First-time setup detected: Installing required Node.js packages...
    echo [SETUP] Running 'npm install' (this takes 10-20 seconds)...
    echo.
    call npm install
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies. Please check your internet connection.
        pause
        exit /b 1
    )
    echo.
    echo [SETUP] Packages installed successfully!
    echo.
)

:: 5. Check if server is already running on port 8510
netstat -ano | findstr 8510 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [INFO] AudioCRM Server is already running on http://localhost:8510.
    echo [INFO] Opening KYC Calling app in your default browser...
    start http://localhost:8510
    timeout /t 2 >nul
    exit /b 0
)

:: 6. Launch server and open browser
echo [INFO] Starting local server at http://localhost:8510 ...
echo [INFO] Server Port: 8510
echo [INFO] Local Web: http://localhost:8510
echo [NOTE] Keep this window open or minimized while using the CRM.
echo ======================================================================
echo.

start "" http://localhost:8510
node server.js

pause
