@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS1_PATH=%SCRIPT_DIR%speak-local.ps1"

if "%~1"=="" (
  echo Usage: %~n0 "text to speak" [config_path]
  exit /b 2
)

set "TEXT=%~1"
set "CONFIG=%~2"

if "%CONFIG%"=="" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1_PATH%" -Text "%TEXT%"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1_PATH%" -Text "%TEXT%" -Config "%CONFIG%"
)

exit /b %ERRORLEVEL%
