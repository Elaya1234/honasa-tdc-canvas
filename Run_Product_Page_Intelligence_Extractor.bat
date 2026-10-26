@echo off
title Product Page Intelligence Extractor
color 0D

echo ======================================================================
echo    PRODUCT PAGE INTELLIGENCE EXTRACTOR
echo    AI-Powered Formulation, Claim & Consumer Insight Extractor
echo ======================================================================
echo.

set "UV_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv.exe"
set "PYTHON_EXE=C:\Users\elaya.n\Documents\HONASA TDC\IM 2026 Analyisis\uv_python\cpython-3.14.7-windows-x86_64-none\python.exe"
set "APP_DIR=C:\Users\elaya.n\Documents\HONASA TDC"

cd /d "%APP_DIR%"

"%PYTHON_EXE%" pdp_intelligence.py %*

if %errorlevel% neq 0 (
    echo [INFO] Falling back to UV environment...
    "%UV_EXE%" run --python "%PYTHON_EXE%" --with google-genai python pdp_intelligence.py %*
)

echo.
echo ======================================================================
echo Execution complete.
echo ======================================================================
pause
