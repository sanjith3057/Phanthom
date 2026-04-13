"""
Phantom Fix Script - Run this once to repair the environment.
This patches torchvision out of the transformers import chain and rebuilds pydantic models.
"""
import subprocess
import sys

venv_pip = sys.executable.replace("python.exe", "pip.exe").replace("python", "pip")

print("=== Step 1: Uninstalling conflicting torchvision ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "torchvision", "torchaudio", "-y"])

print("\n=== Step 2: Installing torchvision matching torch 2.5.1+cu121 ===")
subprocess.run([
    sys.executable, "-m", "pip", "install",
    "torchvision==0.20.1+cu121",
    "torchaudio==2.5.1+cu121",
    "--index-url", "https://download.pytorch.org/whl/cu121",
    "--no-deps"
])

print("\n=== Step 3: Pinning pydantic to mergekit-compatible version ===")
subprocess.run([sys.executable, "-m", "pip", "install", "pydantic==2.10.6", "--no-deps"])

print("\n=== Step 4: Test import chain ===")
try:
    import torch
    print(f"  torch: OK ({torch.__version__})")
    import torchvision
    print(f"  torchvision: OK ({torchvision.__version__})")
    from transformers import PretrainedConfig
    print("  transformers.PretrainedConfig: OK")
    from mergekit.config import MergeConfiguration
    print("  mergekit.config: OK")
    print("\n✅ Environment is HEALTHY. Run your mergekit-yaml command now!")
except Exception as e:
    print(f"\n❌ Still broken: {e}")
    print("   Please share this error message.")
