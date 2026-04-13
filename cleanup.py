import os
import shutil

directories_to_clean = [
    "src/app/__pycache__",
    "src/app/tools/__pycache__",
    "outputs"
]

files_to_remove = [
    "outputs/phantom-slerp",
    "outputs/phantom-ties",
    "database/phantom.db"
]

print("🧹 CLEANING CACHE AND INCOMPLETE FILES...")

for d in directories_to_clean:
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
            print(f"✅ Removed directory: {d}")
        except Exception as e:
            print(f"❌ Failed to clear {d}: {e}")

for f in files_to_remove:
    if os.path.exists(f):
        try:
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)
            print(f"✅ Removed: {f}")
        except Exception as e:
            print(f"❌ Failed to clear {f}: {e}")

print("✨ Cleanup Complete! You can safely run your commands again.")
