import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src", "app"))

from forge_reasoning import ForgeEngine
from utils import format_system_prompt

def test_tool_logic():
    # 1. Test Prompt Generation
    print("--- TESTING SYSTEM PROMPT ---")
    sys_prompt = format_system_prompt([])
    if "search_tavily" in sys_prompt and "TOOL_CALL" in sys_prompt:
        print("[SUCCESS] System prompt includes tool definitions.")
    else:
        print("[FAILURE] System prompt missing tool definitions.")

    # 2. Test ForgeEngine Prompt Building
    print("\n--- TESTING FORGE ENGINE PROMPT ---")
    forge = ForgeEngine()
    # Mocking reason to check the prompt it builds
    # We will temporarily patch the llm call to just return the prompt
    def mock_llm(prompt, **kwargs):
        return [{"generated_text": prompt}]
    
    forge.llm = mock_llm
    full_prompt = forge.reason(sys_prompt, "Context: Hi", "What is the latest news about Tamil Nadu?")
    
    if "COGNITIVE ASSESSMENT" in full_prompt and "PHANTOM (THOUGHTS)" in full_prompt:
        print("[SUCCESS] Forge reasoning prompt includes mandate and thought markers.")
    else:
        print("[FAILURE] Forge reasoning prompt missing cognitive assessment.")

if __name__ == "__main__":
    test_tool_logic()
