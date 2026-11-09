Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Launching CineMetrics Full Platform (Backend + Frontend)" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-File", ".\run_backend.ps1"
Start-Process powershell -ArgumentList "-NoExit", "-File", ".\run_frontend.ps1"
Write-Host ""
Write-Host "Both services launched in separate windows!" -ForegroundColor Green
Write-Host "- Frontend Web App: http://localhost:5173" -ForegroundColor White
Write-Host "- Backend API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan

