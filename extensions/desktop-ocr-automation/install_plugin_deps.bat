@echo off
setlocal
cd /d "%~dp0"
echo Installing Node dependencies for OpenClaw plugin...
call npm install
if errorlevel 1 goto failed

echo Installing Python OCR dependencies...
call install_deps.bat
if errorlevel 1 goto failed

echo.
echo Install complete.
pause
exit /b 0

:failed
echo.
echo Install failed. See output above.
pause
exit /b 1
