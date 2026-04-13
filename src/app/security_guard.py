import re

class SecurityGuard:
    """
    Phase F (Filter) & Phase U (Understand/Review).
    Protects against prompt injections, DAN exploits, and token leakage.
    """
    def __init__(self):
        # Basic heuristic filters for the 3B scale where we can't afford a large separate NLP model
        self.banned_phrases = [
            "ignore previous instructions",
            "you are now",
            "system prompt",
            "forget your instructions",
            "sudo",
            "bypass",
            "Developer Mode enabled"
        ]

    def check_input(self, user_input: str) -> tuple[bool, str]:
        """Runs pre-computation Phase F."""
        text = user_input.lower()
        for phrase in self.banned_phrases:
            if phrase in text:
                return False, "SECURITY ALERT: Malicious Prompt Injection Detected. Access Denied."
                
        if len(text) > 4000:
            return False, "SECURITY ALERT: Context Window Overflow Attack attempt. Max 4000 chars."
            
        return True, "Pass"

    def review_output(self, llm_output: str) -> tuple[bool, str]:
        """Runs post-computation Phase U."""
        # Check if the model leaked its internal prompts
        if "You are PHANTOM-3B" in llm_output:
            return False, "[Output generation halted: Internal directives leaked in response]"
            
        return True, llm_output
