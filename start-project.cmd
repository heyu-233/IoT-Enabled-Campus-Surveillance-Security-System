@echo off
setlocal

set "ROOT=%~dp0"
set "PS_SCRIPT=%ROOT%scripts\start-dev-stack.ps1"

if not exist "%PS_SCRIPT%" (
  echo [iot-stack] Missing startup script: "%PS_SCRIPT%"
  pause
  exit /b 1
)

echo [iot-stack] Starting local stack...
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
if errorlevel 1 (
  echo.
  echo [iot-stack] Startup failed. Check logs under ".runtime\logs".
  pause
  exit /b 1
)

echo.
echo [iot-stack] Opening frontend...
start "" "http://127.0.0.1:5173"
exit /b 0
