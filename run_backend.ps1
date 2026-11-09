Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting CineMetrics Backend API Server (FastAPI)" -ForegroundColor Yellow
Write-Host "  API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "  Health:   http://127.0.0.1:8000/api/v1/health" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

