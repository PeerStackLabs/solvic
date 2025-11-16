@echo off
echo ====================================
echo Stopping Solvic Automation Project
echo ====================================
echo.

echo Stopping Streamlit...
taskkill /FI "WINDOWTITLE eq Streamlit Chatbot*" /F >nul 2>&1

echo Stopping Automation Daemon...
taskkill /FI "WINDOWTITLE eq Automation Daemon*" /F >nul 2>&1

REM Fallback: Kill all Python processes running streamlit or main.py
wmic process where "commandline like '%%streamlit%%' or commandline like '%%main.py%%'" delete >nul 2>&1

timeout /t 1 /nobreak >nul

echo.
echo ====================================
echo ✅ All Services Stopped
echo ====================================
echo.
pause
