try:
    import torch
    import bitsandbytes
    import accelerate
    print(f"Torch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_memory_info(0).total / 1024**3:.2f} GB")
    print("✅ BitsAndBytes imported successfully.")
except ImportError as e:
    print(f"❌ Missing Dependency: {e}")
except Exception as e:
    print(f"❌ Error during check: {e}")
