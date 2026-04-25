@echo off
setlocal

set "ROOT=%~dp0"
set "PS_SCRIPT=%ROOT%scripts\stop-dev-stack.ps1"

if not exist "%PS_SCRIPT%" (
  echo [iot-stack] Missing shutdown script: "%PS_SCRIPT%"
  pause
  exit /b 1
)

echo [iot-stack] Stopping local stack...
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
if errorlevel 1 (
  echo.
  echo [iot-stack] Shutdown reported an error. Check logs under ".runtime\logs".
  pause
  exit /b 1
)

exit /b 0
