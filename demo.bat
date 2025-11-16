@echo off
echo ====================================
echo Quick Demo - Solvic Project
echo ====================================
echo.

REM Set environment variables
set GEMINI_API_KEY=AIzaSyBQENGIQhrizs8TbMTp433QTzhJ06rtFMQ
set NOTION_API_KEY=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

REM Change to project directory
cd /d "%~dp0"

echo Starting Streamlit Chatbot...
start "Streamlit" C:/Users/manch/AppData/Local/Programs/Python/Python313/python.exe -m streamlit run src/web/chatbot_app.py

echo Waiting for Streamlit to start...
timeout /t 5 /nobreak >nul

echo.
echo ====================================
echo Running Automation (Processing last 1 hour)
echo ====================================
echo.

REM Delete processed transcripts to reprocess demo files
del processed_transcripts.json >nul 2>&1

C:/Users/manch/AppData/Local/Programs/Python/Python313/python.exe src/main.py --hours 1

echo.
echo ====================================
echo ✅ Demo Complete!
echo ====================================
echo.
echo Streamlit Chatbot: http://localhost:8501
echo.
echo Press any key to exit...
pause >nul
