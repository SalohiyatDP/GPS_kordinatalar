@echo off
chcp 65001 >nul
title Aqlli Koordinata va Kadastr Tahlilchisi
setlocal
set "ROOT=%~dp0"

echo ============================================================
echo   Aqlli Koordinata va Kadastr Tahlilchisi - ishga tushirish
echo ============================================================
echo.
echo  Backend (8000) va Frontend (5173) alohida oynalarda
echo  ishga tushiriladi. Brauzer avtomatik ochiladi.
echo.

REM ---------------------------------------------------------------
REM  Backend: venv yaratish, kutubxonalarni o'rnatish, uvicorn
REM ---------------------------------------------------------------
start "Backend - FastAPI" cmd /k "cd /d "%ROOT%backend" && (if not exist .venv python -m venv .venv) && call .venv\Scripts\activate.bat && python -m pip install -q -r requirements.txt && uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM ---------------------------------------------------------------
REM  Frontend: npm install, Vite dev server
REM ---------------------------------------------------------------
start "Frontend - Vite" cmd /k "cd /d "%ROOT%frontend" && (if not exist node_modules npm install) && npm run dev"

REM ---------------------------------------------------------------
REM  Serverlar ko'tarilishini kutib, brauzerni ochish
REM ---------------------------------------------------------------
echo  Serverlar ishga tushmoqda, iltimos kuting...
timeout /t 15 /nobreak >nul
start "" http://localhost:5173

echo.
echo  Tayyor! Brauzerda ochildi: http://localhost:5173
echo  (Yopish uchun ochilgan ikkita oynani yoping yoki Ctrl+C bosing.)
endlocal
