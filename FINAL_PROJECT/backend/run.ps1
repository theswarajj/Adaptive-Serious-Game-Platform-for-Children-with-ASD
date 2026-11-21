# SkillSpark Backend PowerShell Launcher
# Runs FastAPI backend using Python 3.10 where fastapi, opencv, mediapipe are installed.
Set-Location $PSScriptRoot

if (Test-Path "C:\Program Files\Python310\python.exe") {
    Write-Host "Starting FastAPI Backend with Python 3.10..." -ForegroundColor Cyan
    & "C:\Program Files\Python310\python.exe" app.py
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    Write-Host "Starting FastAPI Backend with py -3.10..." -ForegroundColor Cyan
    & py -3.10 app.py
} else {
    Write-Host "Starting FastAPI Backend with python..." -ForegroundColor Yellow
    python app.py
}

