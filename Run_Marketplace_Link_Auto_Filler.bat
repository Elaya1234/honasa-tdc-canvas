@echo off
title Marketplace Link Auto-Filler
color 0B

echo ======================================================================
echo    MARKETPLACE LINK AUTO-FILLER
echo    Autonomous AI-powered link finder and Excel auto-filler
echo ======================================================================
echo.

set "UV_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe"
set "PYTHON_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe"
set "APP_DIR=C:\Users\elaya.n\Documents\HONASA TDC"

cd /d "%APP_DIR%"

echo [INFO] Running Marketplace Link Auto-Filler...
"%PYTHON_EXE%" gso_master_autofill.py %*

if %errorlevel% neq 0 (
    echo [INFO] Falling back to UV environment...
    "%UV_EXE%" run --python "%PYTHON_EXE%" --with openpyxl,curl_cffi,beautifulsoup4,google-genai,pydantic python gso_master_autofill.py %*
)

echo.
echo ======================================================================
echo Execution complete.
echo ======================================================================
pause
