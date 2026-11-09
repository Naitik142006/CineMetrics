@echo off
echo ========================================================
echo   Launching CineMetrics Platform (Backend + Frontend)
echo ========================================================
start "CineMetrics - Backend API" cmd /k "run_backend.bat"
start "CineMetrics - Frontend Web App" cmd /k "run_frontend.bat"
echo.
echo Both services are launching in separate windows!
echo - Frontend UI: http://localhost:5173
echo - Backend API: http://127.0.0.1:8000/docs
echo ========================================================
