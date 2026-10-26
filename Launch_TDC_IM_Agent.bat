@echo off
title TDC - IM Performance Tracking Agent (http://localhost:8504)
color 0B

echo ======================================================================
echo    THE DERMA CO — IM PERFORMANCE TRACKING AGENT
echo    Local URL: http://localhost:8504
echo ======================================================================
echo.

set "UV_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe"
set "PYTHON_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe"
set "APP_DIR=C:\Users\elaya.n\Documents\HONASA TDC"

cd /d "%APP_DIR%"

:: Check if the server is already active on port 8504
netstat -ano | findstr 8504 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [INFO] Server is already running on http://localhost:8504.
    echo [INFO] Opening web app in your default browser...
    start http://localhost:8504
    ping 127.0.0.1 -n 3 >nul
    exit
)

echo [INFO] Starting TDC IM Performance Tracking Agent...
echo [INFO] URL: http://localhost:8504
echo [NOTE] Keep this window open or minimized while using the agent.
echo ======================================================================
echo.

:: Launch Streamlit app on port 8504
"%UV_EXE%" run --offline --python "%PYTHON_EXE%" --with streamlit,pandas,openpyxl,google-genai,apify-client,yt-dlp,pydantic,curl_cffi,beautifulsoup4 python -m streamlit run tdc_im_agent/app.py --server.port=8504 --browser.gatherUsageStats=false --server.headless=false
if %errorlevel% neq 0 (
    echo [INFO] Offline launch fallback: connecting to cache...
    "%UV_EXE%" run --python "%PYTHON_EXE%" --with streamlit,pandas,openpyxl,google-genai,apify-client,yt-dlp,pydantic,curl_cffi,beautifulsoup4 python -m streamlit run tdc_im_agent/app.py --server.port=8504 --browser.gatherUsageStats=false --server.headless=false
)

pause
