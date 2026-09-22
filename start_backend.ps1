# CyTrack — Start FastAPI Backend
# Run from the project root: .\start_backend.ps1

Write-Host "Starting CyTrack backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\backend"
& "$PSScriptRoot\.venv\Scripts\uvicorn.exe" main:app --host 127.0.0.1 --port 8000 --reload

