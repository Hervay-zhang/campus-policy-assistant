@echo off
title Stop all - Campus RAG
echo ==================================================
echo  Campus Policy RAG - stop everything
echo  This will close: cpolar tunnel / backend 8002 / frontend 5173
echo ==================================================
echo.
echo Stopping cpolar tunnel ...
taskkill /IM cpolar.exe /F >nul 2>&1
echo Stopping backend 8002 ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /C:":8002" ^| findstr /C:"LISTENING"') do taskkill /PID %%a /F >nul 2>&1
echo Stopping frontend 5173 ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /C:":5173" ^| findstr /C:"LISTENING"') do taskkill /PID %%a /F >nul 2>&1
echo.
echo Done. Public access is now closed.
pause
