@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 (
    echo Install Python 3.12 from python.org, then run this file again.
    pause
    exit /b 1
  )
)
if not exist .venv\netguard-ready (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Setup failed. Check internet connection and Python version.
    pause
    exit /b 1
  )
  echo ready>.venv\netguard-ready
)
.venv\Scripts\python.exe app.py
pause
