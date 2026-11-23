@echo off
title Package KYC Calling Suite for Sharing
color 0A

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0package_kyc.ps1"

echo.
pause
