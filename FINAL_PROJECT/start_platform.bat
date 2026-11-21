@echo off
title SkillSpark Platform Launcher
cd /d "%~dp0"
echo ========================================================
echo   Starting Autism Learning Platform (SkillSpark)
echo ========================================================
echo.

echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "SkillSpark Backend" cmd /k "cd /d %~dp0backend && if exist ""C:\Program Files\Python310\python.exe"" (""C:\Program Files\Python310\python.exe"" app.py) else (py -3.10 app.py || python app.py)"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Vite Frontend on http://localhost:5173 ...
start "SkillSpark Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo   Platform is running!
echo   Frontend: http://localhost:5173/
echo   Backend:  http://localhost:8000/
echo ========================================================
echo.
echo Keep this window open or close it when done.
pause

