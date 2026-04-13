import os
import torch
from safetensors.torch import load_file, save_file
import json
import shutil

# --- CONFIGURATION ---
MODEL_1_DIR = "models/qwen"        # Qwen2.5-3B-Instruct
MODEL_2_DIR = "models/qwen-coder"  # Qwen2.5-Coder-3B-Instruct (Update if path is different)
OUTPUT_DIR = "outputs/phantom-slerp"
RATIO = 0.5  # 50/50 blend

def surgical_merge():
    # 1. Verification
    if not os.path.exists(MODEL_1_DIR):
        print(f"❌ Error: Model 1 not found at {MODEL_1_DIR}")
        return
    if not os.path.exists(MODEL_2_DIR):
        print(f"❌ Error: Model 2 not found at {MODEL_2_DIR}. Please update MODEL_2_DIR in this script.")
        return

    print(f"🏗️ Starting Surgical Merge...")
    print(f"A: {MODEL_1_DIR}")
    print(f"B: {MODEL_2_DIR}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Key Mapping
    # Assuming models have multiple shards (model-00001-of-00002.safetensors)
    index_file = os.path.join(MODEL_1_DIR, "model.safetensors.index.json")
    if not os.path.exists(index_file):
        print("❌ Error: model.safetensors.index.json not found in Model 1.")
        return

    with open(index_file, "r") as f:
        index_data = json.load(f)
    
    weight_map = index_data.get("weight_map", {})
    shards = sorted(list(set(weight_map.values())))
    
    print(f"📦 Identified {len(shards)} shards to process.")

    # 3. Surgical Stitching
    new_weight_map = {}
    
    for shard in shards:
        print(f"🧵 Processing shard: {shard}...")
        shard_path_1 = os.path.join(MODEL_1_DIR, shard)
        shard_path_2 = os.path.join(MODEL_2_DIR, shard)
        
        if not os.path.exists(shard_path_2):
            print(f"⚠️ Warning: {shard} not found in Model 2. Using Model 1 only.")
            weights_1 = load_file(shard_path_1)
            merged_weights = weights_1
        else:
            weights_1 = load_file(shard_path_1)
            weights_2 = load_file(shard_path_2)
            
            merged_weights = {}
            for key in weights_1.keys():
                if key in weights_2:
                    # Mathematical Average (Linear Merge)
                    merged_weights[key] = (weights_1[key] * (1 - RATIO)) + (weights_2[key] * RATIO)
                else:
                    merged_weights[key] = weights_1[key]
            
            # Clean up memory
            del weights_1
            del weights_2
            torch.cuda.empty_cache() if torch.cuda.is_available() else None

        # Save merged shard
        output_shard_path = os.path.join(OUTPUT_DIR, shard)
        save_file(merged_weights, output_shard_path)
        print(f"✅ Saved shard to {output_shard_path}")
        del merged_weights

    # 4. Copy Metadata
    print("📂 Copying configuration and tokenizer files...")
    meta_files = ["config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt", "model.safetensors.index.json"]
    for file in meta_files:
        src = os.path.join(MODEL_1_DIR, file)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUTPUT_DIR, file))

    print("\n🎉 PHANTOM-3B Surgical Merge Complete!")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    surgical_merge()
