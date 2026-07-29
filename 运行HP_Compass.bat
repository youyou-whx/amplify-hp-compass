@echo off
cd /d "%~dp0"

echo ============================================
echo   HP Compass - AMPlify
echo ============================================
echo.
echo [1/2] Running HP Compass pipeline...
echo.

python "scripts\run_hp_compass.py" --input "hp record" --output "hp_compass_output" --deadline 2026-10-01

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Pipeline failed. Check messages above.
    pause
    exit /b 1
)

echo.
echo [OK] Pipeline complete.
echo.
echo [2/2] Launching dashboard...
echo.
start "HP Compass Dashboard" python -m streamlit run "hp_compass\app.py" -- --data "hp_compass_output" --server.port 8501
echo.
echo ============================================
echo   Open http://127.0.0.1:8501 in your browser
echo ============================================
echo.
pause
