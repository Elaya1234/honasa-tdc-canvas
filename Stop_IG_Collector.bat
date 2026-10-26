@echo off
title Stop Instagram Reel Collector Server
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_collector.ps1"
