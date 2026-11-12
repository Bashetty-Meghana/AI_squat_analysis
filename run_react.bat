@echo off
echo ========================================================
echo Starting IronPath AI Squat Form Coach (FastAPI + React)
echo ========================================================
python -m pip install -r requirements.txt
echo Launching FastAPI + React Application on http://localhost:8000...
start http://localhost:8000
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
pause
