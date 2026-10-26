@echo off
title Instagram Reel Intelligence Analyzer (http://localhost:8502)
color 0A

echo ======================================================================
echo    INSTAGRAM REEL INTELLIGENCE ANALYZER
echo    Local URL: http://localhost:8502
echo ======================================================================
echo.

set "UV_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe"
set "PYTHON_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe"
set "APP_DIR=C:\Users\elaya.n\Documents\HONASA TDC\ig_reel_collector"

cd /d "%APP_DIR%"

:: Check if the server is already active on port 8502
netstat -ano | findstr 8502 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [INFO] Server is already running on http://localhost:8502.
    echo [INFO] Opening web app in your default browser...
    start http://localhost:8502
    ping 127.0.0.1 -n 3 >nul
    exit
)

echo [INFO] Starting server and launching web app in your browser...
echo [NOTE] Keep this window open or minimized while using the tool.
echo ======================================================================
echo.

:: Try offline mode first (fastest, no DNS/PyPI dependency, AppLocker safe)
"%UV_EXE%" run --offline --python "%PYTHON_EXE%" --with streamlit,pandas,openpyxl,google-genai,apify-client,yt-dlp,pydantic,curl_cffi,beautifulsoup4 python -m streamlit run app.py --server.port=8502 --browser.gatherUsageStats=false --server.headless=false
if %errorlevel% neq 0 (
    echo [INFO] Offline launch fallback: connecting to verify cache...
    "%UV_EXE%" run --python "%PYTHON_EXE%" --with streamlit,pandas,openpyxl,google-genai,apify-client,yt-dlp,pydantic,curl_cffi,beautifulsoup4 python -m streamlit run app.py --server.port=8502 --browser.gatherUsageStats=false --server.headless=false
)

pause
