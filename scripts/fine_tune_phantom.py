import os
import torch
import gc
import argparse
import sys
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

def flush():
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()

def train_phantom(dry_run=False):
    model_id = "outputs/phantom-slerp"
    output_dir = "outputs/phantom-aligned"
    dataset_path = "datasets/phantom_alignment.jsonl"

    if not os.path.exists(dataset_path):
        print(f"Error: Dataset {dataset_path} not found. Run generate_alignment_data.py first.")
        return

    flush()

    # 1. Load Quantization Config (4-bit for 4GB RAM stability)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    try:
        # 2. Load Model & Tokenizer
        print(f"Loading model for {'DRY RUN' if dry_run else 'ALIGNMENT'}...")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        tokenizer.pad_token = tokenizer.eos_token

        # 3. Prepare for QLoRA
        model = prepare_model_for_kbit_training(model)
        config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        model = get_peft_model(model, config)
        
        # Override config vocab_size to match actual weight matrix dimensions
        actual_vocab_size = model.get_output_embeddings().weight.shape[0]
        print(f"DEBUG: Overriding config.vocab_size ({model.config.vocab_size}) with actual size ({actual_vocab_size})")
        model.config.vocab_size = actual_vocab_size
        
        # Enable gradient checkpointing for VRAM savings
        model.gradient_checkpointing_enable()

        # 4. Load Dataset
        data = load_dataset("json", data_files=dataset_path, split="train")
        
        def tokenize_function(examples):
            # Create the prompt string
            prompts = [f"Instruction: {i}\nInput: {inp}\nResponse: {o}" for i, inp, o in zip(examples["instruction"], examples["input"], examples["output"])]
            
            # Tokenize and ensure consistent length
            tokenized = tokenizer(
                prompts, 
                padding="max_length", 
                truncation=True, 
                max_length=512,
                return_tensors=None
            )
            
            # For Causal LM, labels are typically a copy of input_ids
            tokenized["labels"] = tokenized["input_ids"].copy()
            
            return tokenized

        tokenized_data = data.map(tokenize_function, batched=True, remove_columns=data.column_names)

        # 5. Training Arguments (Aggressive VRAM Savings)
        training_args = TrainingArguments(
            output_dir=output_dir if not dry_run else "outputs/dry_run",
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            warmup_steps=2 if dry_run else 10,
            max_steps=1 if dry_run else 50, 
            learning_rate=2e-4,
            fp16=True,
            logging_steps=1,
            optim="paged_adamw_32bit",
            save_strategy="no",
            report_to="none",
            remove_unused_columns=False # Important when using custom labels
        )

        # 6. Execute Training
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_data,
        )

        print(f"--- PHANTOM {'DRY RUN' if dry_run else 'ALIGNMENT'} STARTED ---")
        trainer.train()
        
        if dry_run:
            print("\n✅ DRY RUN SUCCESSFUL. VRAM footprint is stable.")
            return

        # 7. Save PEFT Adapter
        model.save_pretrained(output_dir)
        print(f"Alignment complete. Adapter saved to {output_dir}")

    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print("\nCRITICAL: GPU Out Of Memory. Fine-tuning aborted for safety.")
            flush()
        else:
            raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run 1 step to test VRAM overhead")
    args = parser.parse_args()
    
    train_phantom(dry_run=args.dry_run)
