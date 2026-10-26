@echo off
title Exact SKU Marketplace Link Finder (http://localhost:8503)
color 0E

echo ======================================================================
echo    EXACT SKU MARKETPLACE LINK FINDER
echo    Local URL: http://localhost:8503
echo ======================================================================
echo.

set "UV_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe"
set "PYTHON_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe"
set "APP_DIR=C:\Users\elaya.n\Documents\HONASA TDC\skuscout"

cd /d "%APP_DIR%"

:: Check if server is already running on port 8503
netstat -ano | findstr 8503 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [INFO] Server is already running on http://localhost:8503.
    echo [INFO] Opening web app in your default browser...
    start http://localhost:8503
    ping 127.0.0.1 -n 3 >nul
    exit
)

echo [INFO] Starting server and launching web app in your browser...
echo [NOTE] Keep this window open or minimized while using the tool.
echo ======================================================================
echo.

"%PYTHON_EXE%" -m streamlit run app.py --server.port=8503 --browser.gatherUsageStats=false --server.headless=false

if %errorlevel% neq 0 (
    echo [INFO] Falling back to UV runtime engine...
    "%UV_EXE%" run --python "%PYTHON_EXE%" --with streamlit,curl_cffi,beautifulsoup4,pandas,openpyxl,tabulate python -m streamlit run app.py --server.port=8503 --browser.gatherUsageStats=false --server.headless=false
)

pause
