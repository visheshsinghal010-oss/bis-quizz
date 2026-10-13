@echo off
title Bureau of Indian Standards (BIS) Quiz Server
color 0A
echo ================================================================
echo        BUREAU OF INDIAN STANDARDS (BIS) QUIZ APPLICATION        
echo ================================================================
echo.
echo Starting BIS Quiz Server...
echo Opening Host Dashboard in your default browser...
echo.
cd /d "%~dp0"
start "" "http://localhost:5000/host"
python app.py
pause
