@echo off
setlocal
cd /d %~dp0\..

echo Starting WTCalculator (PowerShell)...
powershell -ExecutionPolicy Bypass -File .\scripts\start_windows.ps1
