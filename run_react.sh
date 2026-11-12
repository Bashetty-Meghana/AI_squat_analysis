#!/bin/bash
echo "========================================================"
echo "Starting IronPath AI Squat Form Coach (FastAPI + React)"
echo "========================================================"
pip install -r requirements.txt
echo "Launching FastAPI + React Application on http://localhost:8000..."
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
