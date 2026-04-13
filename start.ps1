# PHANTOM-3B Launch Script (PowerShell)
# Run from project root: .\start.ps1

Write-Host "⚡ PHANTOM-3B — Initializing..." -ForegroundColor Cyan

# Ensure directories exist
New-Item -ItemType Directory -Force -Path "outputs\phantom-slerp" | Out-Null
New-Item -ItemType Directory -Force -Path "outputs\phantom-ties"  | Out-Null
New-Item -ItemType Directory -Force -Path "outputs\files"         | Out-Null
New-Item -ItemType Directory -Force -Path "database"              | Out-Null

# Copy .env if missing
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "📋 Created .env — edit it to add your HF_TOKEN if needed." -ForegroundColor Yellow
}

Write-Host "✅ Environment ready." -ForegroundColor Green
Write-Host "🚀 Launching JARVIS Interface at http://localhost:8502" -ForegroundColor Cyan

# Launch Streamlit securely through Python module
python -m streamlit run src/app/main.py --server.port 8502 --server.headless false
