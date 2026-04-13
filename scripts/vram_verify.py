import torch
import sys

def verify_vram():
    print("--- PHANTOM VRAM SAFETY CHECK ---")
    if not torch.cuda.is_available():
        print("CRITICAL: CUDA is not available. Training is not possible.")
        sys.exit(1)
    
    device = 0
    props = torch.cuda.get_device_properties(device)
    total_memory = props.total_memory / (1024**3)
    allocated_memory = torch.cuda.memory_allocated(device) / (1024**3)
    reserved_memory = torch.cuda.memory_reserved(device) / (1024**3)
    free_memory = total_memory - reserved_memory
    
    print(f"Device: {props.name}")
    print(f"Total VRAM: {total_memory:.2f} GB")
    print(f"Allocated:  {allocated_memory:.2f} GB")
    print(f"Free:       {free_memory:.2f} GB")
    
    # Threshold for 4GB systems
    if total_memory < 4.5:
        print("\nWARNING: You are on a memory-constrained system (4GB).")
        if free_memory < 1.0:
            print("DANGER: Less than 1GB free VRAM. Close all heavy apps (Epic Games, Discord, Browser).")
        else:
            print("STATUS: VRAM is tight but potentially workable for QLoRA.")
    
    if free_memory < 0.5:
        print("CRITICAL: Not enough VRAM for even a dry-run. Aborting.")
        sys.exit(1)
    
    print("\n--- SAFETY CHECK PASSED ---")

if __name__ == "__main__":
    verify_vram()
