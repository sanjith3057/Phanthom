#!/bin/bash
# setup.sh - Environment preparation
echo "Initializing PHANTOM-3B Environment..."
pip install -r requirements.txt
echo "Downloading Models Phase 1..."
# Uses huggingface-cli
huggingface-cli download Qwen/Qwen2.5-3B-Instruct --local-dir models/qwen
huggingface-cli download microsoft/Phi-3.5-mini-instruct --local-dir models/phi
echo "Environment Setup Complete!"
