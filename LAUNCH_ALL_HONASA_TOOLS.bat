@echo off
title HONASA Intelligence & E-Commerce Suite
color 0F

:menu
cls
echo ======================================================================
echo           HONASA CONSUMER - INTELLIGENCE & E-COMMERCE SUITE
echo ======================================================================
echo.
echo  [1] Product Data & Media Downloader           (Port 8501)
echo  [2] Exact SKU Marketplace Link Finder         (Port 8503)
echo  [3] Instagram Reel Intelligence Analyzer       (Port 8502)
echo  [4] Product Page Competitive Comparison       (Visual Dashboard)
echo  [5] Marketplace Link Auto-Filler              (GSO Excel Verifier)
echo  [6] Product Page Intelligence Extractor       (Gemini AI Science)
echo  [7] TDC - IM Performance Tracking Agent         (Port 8504)
echo.
echo  [8] Create / Update Desktop Shortcuts for All Tools
echo  [9] Open HONASA Project Directory in Explorer
echo  [0] Exit
echo.
echo ======================================================================
set /p choice="Enter your choice [0-9]: "

if "%choice%"=="1" (
    start "" "Launch_Product_Data_Media_Downloader.bat"
    goto menu
)
if "%choice%"=="2" (
    start "" "Launch_Exact_SKU_Marketplace_Link_Finder.bat"
    goto menu
)
if "%choice%"=="3" (
    start "" "Launch_Instagram_Reel_Intelligence_Analyzer.bat"
    goto menu
)
if "%choice%"=="4" (
    start "" "Launch_Product_Page_Competitive_Comparison.bat"
    goto menu
)
if "%choice%"=="5" (
    start "" "Run_Marketplace_Link_Auto_Filler.bat"
    goto menu
)
if "%choice%"=="6" (
    start "" "Run_Product_Page_Intelligence_Extractor.bat"
    goto menu
)
if "%choice%"=="7" (
    start "" "Launch_TDC_IM_Agent.bat"
    goto menu
)
if "%choice%"=="8" (
    powershell -ExecutionPolicy Bypass -File "create_all_shortcuts.ps1"
    pause
    goto menu
)
if "%choice%"=="9" (
    explorer "C:\Users\elaya.n\Documents\HONASA TDC"
    goto menu
)
if "%choice%"=="0" (
    exit
)

echo Invalid choice. Please try again.
ping 127.0.0.1 -n 2 >nul
goto menu
