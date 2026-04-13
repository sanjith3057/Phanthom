# PHANTOM-3B — Full Dependency Installer
# Run this once inside your (mergekit-env) to get everything working.

Write-Host "⚡ Installing PHANTOM-3B dependencies..." -ForegroundColor Cyan

# Uninstall the broken 'docx' package
pip uninstall -y docx 2>$null

# Install correct packages
pip install `
    streamlit `
    python-docx `
    fpdf `
    requests `
    python-dotenv `
    psutil `
    accelerate `
    bitsandbytes

Write-Host "✅ All dependencies installed. Run .\start.ps1 to launch." -ForegroundColor Green
