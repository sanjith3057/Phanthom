import json
import random

def generate_dataset():
    tasks = [
        "face recognition app", "distributed logging system", "real-time object detection",
        "stock market predictor", "voice-to-text transcriber", "secure password manager",
        "multi-agent orchestration", "edge-based anomaly detector", "lightweight vector db",
        "low-latency chat api", "automated pdf extractor", "dockerized microservice"
    ]
    
    constraints = [
        "4GB VRAM", "500ms latency", "2GB RAM overhead", "low-power CPU",
        "offline environment", "no cloud access", "job-seeker budget"
    ]
    
    architectures = [
        "OpenCV", "GGUF 4-bit", "FastAPI", "SQLite", "ONNX Runtime",
        "LangGraph", "Docker Slim", "Redis", "DuckDB", "Flatbuffers"
    ]

    dataset = []
    
    for i in range(200):
        task = random.choice(tasks)
        constraint = random.choice(constraints)
        arch = random.choice(architectures)
        
        # Crafting high-tier Q&A
        question = f"Design a {task} considering a {constraint} limitation."
        
        if "4GB" in constraint or "RAM" in constraint:
            answer = (
                f"PHANTOM PROTOCOL: To deploy a {task} on {constraint}, use a deterministic mapping. "
                f"Avoid heavy transformers. Implement {arch} for efficient processing. "
                f"Store persistent data in SQLite to keep VRAM clear for model weights. "
                f"Use KV Cache quantization if using a 3B LLM core."
            )
        else:
            answer = (
                f"PHANTOM ARCHITECTURE: For {task} with {constraint}, prioritize {arch}. "
                f"Implement asynchronous I/O to maintain the latency window. "
                "Decompose the task into LangGraph micro-nodes to prevent token overflow. "
                "Ensure all binary assets are stored as Flatbuffers for fast deserialization."
            )
            
        dataset.append({
            "instruction": question,
            "response": answer
        })

    with open("datasets/phantom_fine_tune.jsonl", "w", encoding="utf-8") as f:
        for entry in dataset:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Dataset Generated: 200 Q&A pairs in datasets/phantom_fine_tune.jsonl")

if __name__ == "__main__":
    import os
    if not os.path.exists("datasets"):
        os.makedirs("datasets")
    generate_dataset()
