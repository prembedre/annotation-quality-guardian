@echo off
setlocal
cd /d "%~dp0.."
set PYTHONPATH=backend;scoring;.

set PYTHON_EXE=C:\Users\LENOVO\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo Starting FastAPI Backend on http://127.0.0.1:8000...
start "AQG Backend" "%PYTHON_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend

echo Starting Vite React Frontend on http://localhost:5173...
start "AQG Frontend" cmd /c "npm --prefix frontend run dev"

echo.
echo ========================================================
echo  Annotation Quality Guardian is RUNNING on localhost!
echo ========================================================
echo   Frontend Dashboard : http://localhost:5173
echo   Backend API        : http://127.0.0.1:8000
echo   Health Status      : http://127.0.0.1:8000/health
echo   Swagger Docs       : http://127.0.0.1:8000/docs
echo ========================================================
echo.
pause
