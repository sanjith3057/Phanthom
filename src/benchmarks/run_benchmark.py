import json
import argparse
import os
import time

def run_benchmark(model_path, questions_path, output_path):
    print(f"Loading '{model_path}' for benchmark...")
    
    # Mock LLM behavior if testing locally without hardware
    if model_path == "Mock":
        print("Running in Mock Mode. Skipping real LLM inference.")
        time.sleep(2)  # Simulate some latency
        
        with open(questions_path, 'r') as f:
            questions = json.load(f)
            
        results = {}
        for q in questions:
            # Fake answers for mock evaluation
            print(f"Evaluating {q['id']}...")
            time.sleep(0.5)
            # Randomly guess if mock is right or wrong, 80% correct
            is_correct = (hash(q['question']) % 10) < 8
            results[q['id']] = {
                "question": q["question"],
                "category": q["category"],
                "passed": is_correct,
                "response": "This is a mock LLM response that was deemed " + ("correct" if is_correct else "incorrect") + "."
            }
            
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Mock benchmark complete. Results saved to {output_path}")
        return
        
    try:
        from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch

        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        quant_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16) if torch.cuda.is_available() else None
        model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            device_map="auto" if torch.cuda.is_available() else None, 
            quantization_config=quant_config,
            trust_remote_code=True
        )
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)
        
        with open(questions_path, 'r') as f:
            questions = json.load(f)
            
        results = {}
        for q in questions:
            print(f"Evaluating {q['id']}...")
            prompt = f"User: Answer this precisely without extra talk.\n{q['question']}\n\nPHANTOM:"
            try:
                response = pipe(prompt, do_sample=False)[0]['generated_text']
                if "PHANTOM:" in response:
                    response = response.split("PHANTOM:")[-1].strip()
            except Exception as e:
                response = f"[Error generating response: {str(e)}]"
                
            # Basic keyword evaluation - real-world would use LLM-as-a-judge
            # This is a proxy evaluation for demo purposes
            passed = q["expected_concept"].lower() in response.lower()
            
            results[q['id']] = {
                "question": q["question"],
                "category": q["category"],
                "passed": passed,
                "response": response
            }
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4)
            
        print(f"Benchmark complete. Results saved to {output_path}")
        
    except ImportError as e:
        print(f"Error importing ML libraries. Ensure transformers & torch are installed. Detail: {e}")
    except Exception as e:
        print(f"Fatal error during benchmark: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PHANTOM-3B benchmarks")
    parser.add_argument("--model", type=str, required=True, help="Path to model or 'Mock'")
    parser.add_argument("--questions", type=str, default="src/benchmarks/questions.json", help="Path to questions JSON")
    parser.add_argument("--output", type=str, required=True, help="Output JSON path")
    
    args = parser.parse_args()
    run_benchmark(args.model, args.questions, args.output)
