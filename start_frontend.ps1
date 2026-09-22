# CyTrack — Start Streamlit Frontend
# Run from the project root: .\start_frontend.ps1

Write-Host "Starting CyTrack frontend on http://localhost:8501 ..." -ForegroundColor Cyan
& "$PSScriptRoot\.venv\Scripts\streamlit.exe" run "$PSScriptRoot\frontend\app.py" --server.port 8501

