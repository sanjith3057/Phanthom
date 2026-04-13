Write-Host "Initializing PHANTOM-3B Environment..."
pip install -r requirements.txt
Write-Host "Downloading Models Phase 1..."
huggingface-cli download Qwen/Qwen2.5-3B-Instruct --local-dir models/qwen
huggingface-cli download microsoft/Phi-3.5-mini-instruct --local-dir models/phi
Write-Host "Environment Setup Complete!"
