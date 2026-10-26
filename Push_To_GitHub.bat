@echo off
title HONASA TDC - Push to GitHub (Elaya1234/honasa-tdc-canvas)
color 0b
echo ======================================================================
echo           HONASA TDC Research Canvas - Pushing to GitHub
echo ======================================================================
echo.
echo Target Repository:
echo https://github.com/Elaya1234/honasa-tdc-canvas.git
echo.

cd /d "C:\Users\elaya.n\Documents\HONASA TDC"

echo Configuring Git Remote...
"C:\Users\elaya.n\Documents\HONASA TDC\tools\git\cmd\git.exe" remote remove origin 2>nul
"C:\Users\elaya.n\Documents\HONASA TDC\tools\git\cmd\git.exe" remote add origin https://github.com/Elaya1234/honasa-tdc-canvas.git
"C:\Users\elaya.n\Documents\HONASA TDC\tools\git\cmd\git.exe" branch -M main

echo.
echo Pushing website to GitHub main branch...
echo (A browser popup may appear asking you to Sign in / Authorize GitHub - please click Authorize)
echo.
"C:\Users\elaya.n\Documents\HONASA TDC\tools\git\cmd\git.exe" push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ----------------------------------------------------------------------
    echo [NOTE] If push failed due to authentication, you can also use a Personal
    echo Access Token (PAT) as your password from https://github.com/settings/tokens
    echo ----------------------------------------------------------------------
    echo.
) else (
    echo.
    echo ======================================================================
    echo SUCCESS! Project files pushed to GitHub successfully!
    echo.
    echo Final Step - Enable GitHub Pages (30 seconds):
    echo 1. Open: https://github.com/Elaya1234/honasa-tdc-canvas/settings/pages
    echo 2. Under "Build and deployment" -> "Branch":
    echo    - Select: "main"
    echo    - Folder: "/ (root)"
    echo 3. Click "Save"
    echo Your sites will be LIVE in 1-2 minutes at:
    echo 👉 Tools Hub: https://elaya1234.github.io/honasa-tdc-canvas/hub.html 👈
    echo 👉 Research Canvas: https://elaya1234.github.io/honasa-tdc-canvas/ 👈
    echo 👉 Sunscreen Board: https://elaya1234.github.io/honasa-tdc-canvas/Sunscreen_Comparison_Board_v3.html 👈
    echo ======================================================================
)

pause
