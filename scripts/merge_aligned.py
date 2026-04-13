import torch
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import shutil

def merge_and_stitch():
    base_model_path = "outputs/phantom-slerp"
    adapter_path = "outputs/phantom-aligned"
    save_path = "outputs/phantom-final"

    print("--- PHANTOM FINAL STITCH: CPU MERGE STARTED ---")
    
    if not os.path.exists(adapter_path):
        print(f"Error: Adapter not found at {adapter_path}")
        return

    # 1. Load Base Model on CPU (16-bit to avoid quantization artifacts during merge)
    print(f"Loading base model from {base_model_path} on CPU...")
    # We use low_cpu_mem_usage and torch_dtype=float16 for stability
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,
        device_map="cpu",
        trust_remote_code=True,
        ignore_mismatched_sizes=True
    )
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)

    # 2. Load Adapter and Merge
    print(f"Applying adapter from {adapter_path}...")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    
    # Force the vocab size override before merging to ensure consistency
    actual_vocab_size = model.get_output_embeddings().weight.shape[0]
    model.config.vocab_size = actual_vocab_size
    
    print("Merging weights (This may take a few minutes on CPU)...")
    model = model.merge_and_unload()

    # 3. Save Final Model
    print(f"Saving stitched model to {save_path}...")
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    
    # Copy config files just in case
    for filename in ["config.json", "generation_config.json"]:
        src = os.path.join(base_model_path, filename)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(save_path, filename))

    print(f"\n✅ STITCH COMPLETE: Aligned model is ready at {save_path}")
    print("You can now select 'PHANTOM-3B (Final Stitch)' in the dashboard.")

if __name__ == "__main__":
    merge_and_stitch()
