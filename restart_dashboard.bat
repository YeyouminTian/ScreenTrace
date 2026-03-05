@echo off
echo ====================================
echo Cleaning Python cache and restarting
echo ====================================

echo.
echo Step 1: Stopping Python processes...
taskkill /F /IM python.exe 2>nul

echo.
echo Step 2: Cleaning __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo.
echo Step 3: Cleaning .pyc files...
del /s /q *.pyc 2>nul

echo.
echo Step 4: Starting Web Dashboard...
echo ====================================
python run_dashboard.py

pause
