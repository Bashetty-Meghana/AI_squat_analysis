#!/usr/bin/env bash
echo "========================================================"
echo "Starting AI Squat Analysis Application (Starting Strength)"
echo "========================================================"
python3 -m pip install -r requirements.txt
echo "Launching Streamlit web application on http://localhost:8501..."
python3 -m streamlit run app.py --server.port 8501
