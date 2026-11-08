# AQG Localhost Startup Script
$rootDir = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $rootDir

$pythonExe = "C:\Users\LENOVO\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { $pythonExe = $pythonCmd.Source }
}

$env:PYTHONPATH = "$rootDir\backend;$rootDir\scoring;$rootDir"

Write-Host "Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
$backendProc = Start-Process -FilePath $pythonExe -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend" -WorkingDirectory $rootDir -PassThru

Write-Host "Starting Vite React Frontend on http://localhost:5173..." -ForegroundColor Cyan
$frontendProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm --prefix frontend run dev" -WorkingDirectory $rootDir -PassThru

Start-Sleep -Seconds 3

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host " Annotation Quality Guardian is RUNNING on localhost! " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Frontend Dashboard : http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API        : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  Health Status      : http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host "  Swagger Docs       : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "========================================================`n" -ForegroundColor Green
