@echo off
echo ============================================================
echo   CineMetrics 2.0 - Quantitative Cinema Intelligence Suite
echo ============================================================
echo.
echo [1/2] Launching FastAPI Backend on http://localhost:8000 ...
start "CineMetrics API (FastAPI)" cmd /k "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Launching React Vite Frontend on http://localhost:5173 ...
start "CineMetrics UI (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================================
echo  Both services launched in separate windows!
echo  - 3D Animated Landing & Terminal UI: http://localhost:5173
echo  - Interactive Swagger API Docs:      http://localhost:8000/docs
echo ============================================================
pause
