import os
import shutil

def rename_and_move():
    moves = [
        ("architecture.md", "docs/architecture.md"),
        ("decisions.md", "docs/decisions.md"),
        ("merge-guide.md", "docs/runbooks/merge-guide.md"),
        ("SKILL (1).md", "skills/reasoning/SKILL.md"),
        ("SKILL.md", "skills/frontend/SKILL.md"),
        ("PRODUCT.md", "PRODUCT.md"),
        ("BUDGET.md", "BUDGET.md"),
        ("SECURITY.md", "SECURITY.md"),
        ("README.md", "README.md"),
        ("PHANTOM.md", "PHANTOM.md"),
    ]
    
    dirs_to_create = [
        "docs/runbooks",
        "src/mergekit",
        "src/benchmarks",
        "src/app/tools",
        "outputs/files",
        "database",
        "skills/reasoning",
        "skills/model-merging",
        "skills/frontend",
        "skills/benchmarking",
        "tools/scripts",
        "tools/prompts"
    ]
    
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")
        
    for src, dst in moves:
        if os.path.exists(src) and src != dst:
            shutil.move(src, dst)
            print(f"Moved {src} -> {dst}")
        elif not os.path.exists(src) and src != dst:
            print(f"File not found: {src}")

if __name__ == "__main__":
    rename_and_move()
    print("Reorganization complete!")
