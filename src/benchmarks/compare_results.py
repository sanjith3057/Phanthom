import json
import argparse
import os

def generate_comparison_table(results_files, output_path):
    print("Generating comparison table...")
    
    table_data = {}
    models = []
    
    for fpath in results_files:
        if not os.path.exists(fpath):
            print(f"Warning: {fpath} not found. Skipping.")
            continue
            
        model_name = os.path.basename(fpath).replace("benchmark_", "").replace(".json", "")
        models.append(model_name)
        
        with open(fpath, 'r') as f:
            data = json.load(f)
            
        # Tally totals
        category_scores = {}
        for q_id, info in data.items():
            cat = info["category"]
            if cat not in category_scores:
                category_scores[cat] = {"passed": 0, "total": 0}
            category_scores[cat]["total"] += 1
            if info["passed"]:
                category_scores[cat]["passed"] += 1
                
        table_data[model_name] = category_scores

    if not table_data:
        print("No valid results found. Cannot generate table.")
        return

    # Extract dynamic categories based on first available model
    categories = list(table_data[models[0]].keys())
    
    table_lines = [
        "## PHANTOM-3B Benchmark Comparison",
        "",
        f"| Model | {' | '.join(categories)} | Total Score |",
        f"|---|{'---|'*len(categories)}---|"
    ]
    
    for model in models:
        row = [model]
        total_p = 0
        total_t = 0
        for cat in categories:
            stats = table_data[model].get(cat, {"passed": 0, "total": 0})
            p, t = stats["passed"], stats["total"]
            total_p += p
            total_t += t
            # Simple visualization
            viz = "✓" * p + "✗" * (t - p)
            row.append(f"{p}/{t} {viz}")
            
        row.append(f"**{total_p}/{total_t}**")
        table_lines.append("| " + " | ".join(row) + " |")

    table_md = "\n".join(table_lines) + "\n"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(table_md)
        
    print(f"Comparison table saved to {output_path}")
    print(table_md.encode('utf-8').decode('cp1252', errors='replace'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", nargs="+", required=True, help="List of benchmark JSON files")
    parser.add_argument("--output", type=str, required=True, help="Output markdown table path")
    
    args = parser.parse_args()
    generate_comparison_table(args.results, args.output)
