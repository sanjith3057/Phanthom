# Runbook: Model Merging Guide
## Step-by-Step PHANTOM-3B Merge Instructions

> *"Senku's protocol: no magic, only method. If you follow this guide exactly, the merge works."*

This runbook is the definitive step-by-step guide for running PHANTOM-3B merges. Use this when:
- Running the merge for the first time
- Re-running with tuned parameters after a poor benchmark result
- Onboarding someone else to the project
- Recovering from a failed merge

---

## Prerequisites Checklist

Before starting, verify everything:

```
☐ Python 3.10+ installed
☐ Virtual environment created and activated
☐ 20GB+ free disk space
☐ 16GB+ RAM
☐ MergeKit installed: `pip show mergekit` → should show version
☐ Transformers installed: `pip show transformers` → should show version
☐ Parent models downloaded:
    ☐ models/qwen/config.json exists
    ☐ models/phi/config.json exists
☐ Output directories exist:
    ☐ outputs/phantom-slerp/ (can be empty)
    ☐ outputs/phantom-ties/  (can be empty)
```

If anything is missing: `bash tools/scripts/setup.sh`

---

## Part 1: SLERP Merge

### Step 1.1 — Verify YAML config

```bash
cat src/mergekit/phantom-slerp.yaml
```

Expected output:
```yaml
models:
  - model: ./models/qwen
    parameters:
      weight: 1.0
  - model: ./models/phi
    parameters:
      weight: 1.0

merge_method: slerp
base_model: ./models/qwen

parameters:
  t:
    - filter: self_attn
      value: 0.5
    - filter: mlp
      value: 0.4
    - value: 0.5

dtype: bfloat16
tokenizer_source: union
```

### Step 1.2 — Run SLERP merge

```bash
# With GPU (recommended if RTX 2050 available):
mergekit-yaml src/mergekit/phantom-slerp.yaml outputs/phantom-slerp \
  --cuda \
  --copy-tokenizer \
  --allow-crimes

# CPU only (if GPU unavailable):
mergekit-yaml src/mergekit/phantom-slerp.yaml outputs/phantom-slerp \
  --copy-tokenizer \
  --allow-crimes \
  --low-cpu-mem-usage
```

**Expected runtime:**
- GPU: 8–12 minutes
- CPU: 15–22 minutes

**Expected terminal output:**
```
Loading model ./models/qwen...
Loading model ./models/phi...
Merging layers: 100%|████████████████| 32/32 [08:23<00:00]
Writing output...
Copying tokenizer...
Done. Output: outputs/phantom-slerp/
```

### Step 1.3 — Verify SLERP output

```bash
# Check files exist
ls -lh outputs/phantom-slerp/

# Expected:
# -rw-r--r-- 1 user user 6.4G model.safetensors
# -rw-r--r-- 1 user user 1.2K config.json
# -rw-r--r-- 1 user user 2.8M tokenizer.json
# -rw-r--r-- 1 user user  845 tokenizer_config.json

# Sanity check — generate one response
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

tok = AutoTokenizer.from_pretrained('./outputs/phantom-slerp')
model = AutoModelForCausalLM.from_pretrained(
    './outputs/phantom-slerp',
    torch_dtype=torch.bfloat16,
    device_map='auto'
)

msgs = [{'role': 'user', 'content': 'What is 17 multiplied by 23?'}]
prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
inputs = tok(prompt, return_tensors='pt').to(model.device)
out = model.generate(**inputs, max_new_tokens=50, temperature=0.0, do_sample=False)
response = tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
print('PHANTOM-SLERP says:', response)
"
```

**Pass criteria:** Model generates coherent text (even if the math answer is wrong). Incoherent output (repeated tokens, empty response) = merge failure → see Troubleshooting.

---

## Part 2: TIES + DARE Merge

### Step 2.1 — Verify YAML config

```bash
cat src/mergekit/phantom-ties-dare.yaml
```

Expected:
```yaml
models:
  - model: ./models/qwen
    parameters:
      density: 0.7
      weight: 1.0
  - model: ./models/phi
    parameters:
      density: 0.7
      weight: 1.0

merge_method: ties
base_model: ./models/qwen

parameters:
  normalize: true
  int8_mask: true

dtype: bfloat16
tokenizer_source: union
```

### Step 2.2 — Run TIES merge

```bash
mergekit-yaml src/mergekit/phantom-ties-dare.yaml outputs/phantom-ties \
  --cuda \
  --copy-tokenizer \
  --allow-crimes \
  --out-shard-size 1B
```

**Expected runtime:** 9–15 minutes (slightly longer than SLERP due to DARE computation)

### Step 2.3 — Verify TIES output

```bash
ls -lh outputs/phantom-ties/

# Same sanity check as SLERP
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
tok = AutoTokenizer.from_pretrained('./outputs/phantom-ties')
model = AutoModelForCausalLM.from_pretrained('./outputs/phantom-ties',
    torch_dtype=torch.bfloat16, device_map='auto')
msgs = [{'role': 'user', 'content': 'Write a one-line Python function to reverse a string.'}]
prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
inputs = tok(prompt, return_tensors='pt').to(model.device)
out = model.generate(**inputs, max_new_tokens=80, temperature=0.0, do_sample=False)
print(tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True))
"
```

---

## Part 3: Running the Full Benchmark

### Step 3.1 — Run benchmark on all 4 models

```bash
# Run this script — it loops through all 4 models
bash tools/scripts/evaluate.sh

# Or run individually:
for model_name in qwen phi phantom-slerp phantom-ties; do
    if [ "$model_name" == "qwen" ]; then
        model_path="./models/qwen"
    elif [ "$model_name" == "phi" ]; then
        model_path="./models/phi"
    else
        model_path="./outputs/$model_name"
    fi

    python src/benchmarks/run_benchmark.py \
        --model "$model_path" \
        --questions src/benchmarks/questions.json \
        --output "outputs/benchmark_${model_name}.json" \
        --device cuda \
        --verbose
done
```

### Step 3.2 — Generate comparison table

```bash
python src/benchmarks/compare_results.py \
    --results outputs/benchmark_qwen.json \
              outputs/benchmark_phi.json \
              outputs/benchmark_phantom-slerp.json \
              outputs/benchmark_phantom-ties.json \
    --output outputs/comparison_table.md

cat outputs/comparison_table.md
```

### Step 3.3 — Find the money shot

```bash
python -c "
import json

results = {}
for name in ['qwen', 'phi', 'phantom-slerp', 'phantom-ties']:
    with open(f'outputs/benchmark_{name}.json') as f:
        results[name] = json.load(f)

for q in results['phantom-ties']['results']:
    qid = q['question_id']
    phantom = q['score']
    qwen = next(r['score'] for r in results['qwen']['results'] if r['question_id'] == qid)
    phi  = next(r['score'] for r in results['phi']['results'] if r['question_id'] == qid)
    if phantom > qwen and phantom > phi:
        print(f'MONEY SHOT — {qid}:')
        print(f'  Qwen: {qwen}, Phi: {phi}, PHANTOM: {phantom}')
        print(f'  Question: {q[\"question\"][:100]}...')
"
```

---

## Part 4: Publishing to HuggingFace

### Step 4.1 — Login

```bash
huggingface-cli login
# Paste token from https://huggingface.co/settings/tokens
# Token needs: write permission
```

### Step 4.2 — Create repository

```bash
huggingface-cli repo create phantom-3b --type model --private
# Change to --public when ready to publish
```

### Step 4.3 — Upload model

```bash
# Install fast upload library first
pip install hf_transfer
export HF_HUB_ENABLE_HF_TRANSFER=1

# Upload (use whichever model scored higher in benchmark)
python -c "
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path='./outputs/phantom-ties',  # or phantom-slerp
    repo_id='YOUR_USERNAME/phantom-3b',
    repo_type='model',
    commit_message='Upload PHANTOM-3B (TIES+DARE merge)'
)
print('Upload complete.')
"
```

### Step 4.4 — Create model card

Create `outputs/phantom-ties/README.md` (HuggingFace uses this as the model card):

```bash
python tools/scripts/generate_model_card.py \
    --model phantom-ties \
    --benchmark outputs/comparison_table.md \
    --output outputs/phantom-ties/README.md
```

---

## Troubleshooting

### Error: OOM during merge

```
RuntimeError: CUDA out of memory
```
**Fix:** Remove `--cuda` flag. Merge runs on CPU (slower but works).

```
MemoryError: Unable to allocate array
```
**Fix:** Add `--low-cpu-mem-usage` flag. Takes longer but avoids peak RAM spike.

---

### Error: Architecture mismatch

```
ValueError: The following keys have mismatched shapes: [...]
```
**Fix:** Verify both models are 3B scale. Check `config.json` in each model directory — `hidden_size` and `num_hidden_layers` must be compatible.

---

### Error: Tokenizer conflict

```
Warning: Tokenizer mismatch between models
```
**Fix:** Ensure `tokenizer_source: union` is in the YAML. Confirm `--copy-tokenizer` flag is passed.

---

### Merged model generates garbage (repeated tokens, empty output)

This means the merge produced incompatible weight distributions — usually from merging architecturally incompatible models.

**Fix sequence:**
1. Verify both models load independently and generate coherent output
2. Switch to SLERP if you were using TIES (simpler merge, less likely to corrupt)
3. Reduce TIES density to 0.8 if SLERP works but TIES doesn't
4. Try `--allow-crimes` flag if not already using it

---

### Benchmark score lower than both parents

Expected this might happen. Tuning protocol:

```
Step 1: Identify which category PHANTOM underperforms
Step 2: Determine which parent is stronger in that category
Step 3: Adjust t for relevant layers toward that parent:
          If reasoning: increase t toward Qwen (reduce from 0.5 toward 0.3)
          If coding: increase t toward Phi (increase from 0.5 toward 0.7)
Step 4: Re-merge with new t value
Step 5: Re-benchmark (only new merge config vs parents, not all 4)
Step 6: If score improves: adopt new config. If not: try density tuning.
```

---

*This runbook should work without modification for the hardware profile documented in BUDGET.md. If running on different hardware, adjust `--cuda` flags and memory flags accordingly.*
