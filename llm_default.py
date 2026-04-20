"""
P H A N T O M — 3 B | Default LLM Template
-----------------------------------------
A robust, 4-bit quantized LLM loader and inference engine.
Includes the 'Params4bit' fix for HF/BNB compatibility.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
import bitsandbytes as bnb
import sys
import os

# --- 1. THE RECOVERY PATCH (Fixes Params4bit initialization error) ---
def apply_bnb_patch():
    if hasattr(bnb.nn.modules, "Params4bit"):
        original_new = bnb.nn.modules.Params4bit.__new__
        def patched_new(cls, *args, **kwargs):
            kwargs.pop("_is_hf_initialized", None)
            kwargs.pop("_is_quantized", None)
            return original_new(cls, *args, **kwargs)
        bnb.nn.modules.Params4bit.__new__ = patched_new
        print("✅ Patch applied: BitsAndBytes compatibility restored.")

apply_bnb_patch()

# --- 2. CONFIGURATION ---
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct" # Replace with your model path
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def load_engine(model_path):
    print(f"🚀 Initializing engine on {DEVICE}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    
    # 4-Bit NormalFloat Quantization (NF4)
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=quant_config if DEVICE == "cuda" else None,
        device_map="auto",
        trust_remote_code=True
    )

    return pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.1
    )

# --- 3. EXECUTION ---
if __name__ == "__main__":
    # Check if a model exists locally, otherwise use the default ID
    target = MODEL_ID
    if len(sys.argv) > 1:
        target = sys.argv[1]

    try:
        pipe = load_engine(target)
        print("\n--- PHANTOM ENGINE READY ---")
        
        while True:
            prompt = input("\n[USER] > ")
            if prompt.lower() in ["exit", "quit"]:
                break
                
            print("\n[PHANTOM] thinking...", end="\r")
            outputs = pipe(prompt)
            response = outputs[0]["generated_text"]
            
            # Simple cleanup of output to show only the new response
            if prompt in response:
                response = response.replace(prompt, "").strip()
            
            print(f"[PHANTOM] > {response}")

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
