@echo off
cd /d "%~dp0"
echo ========================================================
echo   Starting SkillSpark FastAPI Backend (Port 8000)
echo ========================================================
echo.

if exist "C:\Program Files\Python310\python.exe" (
    echo Using Python 3.10 at "C:\Program Files\Python310\python.exe"
    "C:\Program Files\Python310\python.exe" app.py
    goto done
)

py -3.10 app.py
if %errorlevel% equ 0 goto done

python app.py

:done
pause

