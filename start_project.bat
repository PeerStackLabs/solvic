@echo off
echo ====================================
echo Starting Solvic Automation Project
echo ====================================
echo.

REM Set environment variables
set GEMINI_API_KEY=AIzaSyBQENGIQhrizs8TbMTp433QTzhJ06rtFMQ
set NOTION_API_KEY=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

REM Change to project directory
cd /d "%~dp0"

echo [1/2] Starting Streamlit Chatbot...
echo Opening browser at http://localhost:8501
echo.
start "Streamlit Chatbot" C:/Users/manch/AppData/Local/Programs/Python/Python313/python.exe -m streamlit run src/web/chatbot_app.py

REM Wait a moment for Streamlit to start
timeout /t 3 /nobreak >nul

echo [2/2] Starting Automation Daemon...
echo Checking for new transcripts every hour
echo.
start "Automation Daemon" C:/Users/manch/AppData/Local/Programs/Python/Python313/python.exe src/main.py --daemon

echo.
echo ====================================
echo ✅ Project Started Successfully!
echo ====================================
echo.
echo Streamlit Chatbot: http://localhost:8501
echo Automation: Running in background
echo.
echo Press any key to view running processes...
pause >nul

echo.
echo Running processes:
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE

echo.
echo To stop all services, run: stop_project.bat
echo.
pause
