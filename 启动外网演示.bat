@echo off
title Campus RAG - launcher (backend + frontend + tunnel)
cd /d "%~dp0"

echo ==================================================
echo  Campus Policy RAG - public demo launcher
echo  Chain: backend 8002  -^>  frontend 5173  -^>  cpolar tunnel
echo  Keep the backend / frontend / tunnel windows OPEN.
echo  This launcher window can be closed.
echo ==================================================
echo.

echo [1/3] backend on 8002 ...
netstat -ano | findstr /C:":8002" | findstr /C:"LISTENING" >nul 2>&1
if errorlevel 1 (
  start "backend-8002" /D "%~dp0backend" cmd /k "..\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8002"
  timeout /t 12 /nobreak >nul
) else (
  echo   already running - skip
)

echo [2/3] frontend on 5173 ...
netstat -ano | findstr /C:":5173" | findstr /C:"LISTENING" >nul 2>&1
if errorlevel 1 (
  start "frontend-5173" /D "%~dp0frontend" cmd /k "npm run dev"
  timeout /t 10 /nobreak >nul
) else (
  echo   already running - skip
)

echo [3/3] cpolar tunnel ...
echo   Wait about 15 seconds, then copy the https URL printed after
echo   "Tunnel established at" in the cpolar-tunnel window.
start "cpolar-tunnel" /D "D:\tools\cpolar" cmd /k "start-campus.bat"

echo.
echo All steps done. You can close THIS launcher window now.
pause
