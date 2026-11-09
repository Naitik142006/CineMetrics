@echo off
title CineMetrics - Backend Server (FastAPI)
echo ========================================================
echo   Starting CineMetrics Backend API Server (FastAPI)
echo   API Docs: http://127.0.0.1:8000/docs
echo   Health:   http://127.0.0.1:8000/api/v1/health
echo ========================================================
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause

