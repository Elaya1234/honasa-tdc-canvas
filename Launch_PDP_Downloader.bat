@echo off
title Product Data & Media Downloader (http://localhost:8501)
color 0B

echo ======================================================================
echo    PRODUCT DATA & MEDIA DOWNLOADER
echo    Local URL: http://localhost:8501
echo ======================================================================
echo.

set "UV_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe"
set "PYTHON_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe"
set "APP_DIR=C:\Users\elaya.n\Documents\HONASA TDC"

cd /d "%APP_DIR%"

:: Check if server is already running on port 8501
netstat -ano | findstr 8501 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [INFO] Server is already running on http://localhost:8501.
    echo [INFO] Opening web app in your default browser...
    start http://localhost:8501
    ping 127.0.0.1 -n 3 >nul
    exit
)

echo [INFO] Starting server and launching web app in your browser...
echo [NOTE] Keep this window open or minimized while using the tool.
echo ======================================================================
echo.

"%UV_EXE%" run --python "%PYTHON_EXE%" --with streamlit,curl_cffi,beautifulsoup4,pillow,google-genai python -m streamlit run app.py --server.port=8501 --browser.gatherUsageStats=false --server.headless=false

pause
