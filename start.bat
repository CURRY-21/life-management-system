@echo off
echo ========================================
echo Life Management System
echo ========================================
echo.
echo Starting server, please wait...
echo.

cd /d "%~dp0"
python run.py

echo.
echo Server stopped
echo.
pause
