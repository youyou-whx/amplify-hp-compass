Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HP Compass - AMPlify" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Write-Host "[1/2] Processing HP documents..." -ForegroundColor Yellow
python scripts\run_hp_compass.py --input "hp record" --output "hp_compass_output" --deadline 2026-10-01

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR - Check messages above" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`nDone! 11 records processed.`n" -ForegroundColor Green
Write-Host "[2/2] Launching dashboard..." -ForegroundColor Yellow
Start-Process python -ArgumentList '-m','streamlit','run','hp_compass\app.py','--','--data','hp_compass_output','--server.port','8501'

Write-Host "Open in browser: http://127.0.0.1:8501" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to stop"
