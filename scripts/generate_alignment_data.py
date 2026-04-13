import json
import os
import random

def generate_dataset(knowledge_map_path: str, output_path: str):
    """
    Generates a synthetic alignment dataset based on the Technical Ontology.
    """
    with open(knowledge_map_path, "r") as f:
        km = json.load(f)
    
    nodes = km.get("nodes", {})
    dataset = []

    # 1. Generate Hardware-Specific QA
    for name, data in nodes.items():
        if data["type"] == "Hardware":
            # Instruction for Hardware specs
            dataset.append({
                "instruction": f"What are the specifications and optimizations for {name}?",
                "input": "",
                "output": f"The {name} feature {data.get('spec', 'advanced architecture')}. For maximum performance, PHANTOM mandates: {', '.join(data.get('optimizations', []))}. Note: {data.get('warning', 'Follow standard protocols.')}"
            })

    # 2. Generate Constraint/Law QA
    for name, data in nodes.items():
        if data["type"] == "Constraint" or data["type"] == "Requirement":
            dataset.append({
                "instruction": f"How does PHANTOM handle {name}?",
                "input": "",
                "output": f"PHANTOM enforces the following for {name}: {', '.join(data.get('optimizations', []) or data.get('mandates', []) or [])}. Warning: {data.get('warning', 'Mandatory adherence required.')}"
            })

    # 3. Generate Protocol QA
    gh = nodes.get("Global_Heuristics", {})
    if gh:
        dataset.append({
            "instruction": "What are the core laws of the PHANTOM system?",
            "input": "",
            "output": f"PHANTOM follows the Law of Omniscience: {'. '.join(gh.get('rules', []))}."
        })

    # Save to JSONL
    with open(output_path, "w") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")
    
    print(f"Dataset generated with {len(dataset)} examples at {output_path}")

if __name__ == "__main__":
    KM_PATH = "src/app/knowledge_map.json"
    OUT_PATH = "datasets/phantom_alignment.jsonl"
    os.makedirs("datasets", exist_ok=True)
    generate_dataset(KM_PATH, OUT_PATH)
