@echo off
echo ========================================================
echo Starting AI Squat Analysis Application (Starting Strength)
echo ========================================================
python -m pip install -r requirements.txt
echo Launching Streamlit web application on http://localhost:8501...
python -m streamlit run app.py --server.port 8501
pause
