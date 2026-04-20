import json
import os
from datetime import datetime
from utils import count_tokens, PHANTOM_BRAIN


class ForgeEngine:
    """
    Phase R (Reason) & Phase O (Observe) of the FORUM Protocol.
    Determines reasoning path and injects deterministic context from the Ontology.
    """
    def __init__(self, llm_pipeline=None):
        self.llm = llm_pipeline
        self.knowledge_map = self._load_knowledge_map()

    def _load_knowledge_map(self):
        """Loads the Technical Ontology from src/app/knowledge_map.json."""
        try:
            path = os.path.join(os.path.dirname(__file__), "knowledge_map.json")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"nodes": {}}

    def search_knowledge_map(self, query: str) -> str:
        """Extracts technical facts using recursive edge mapping."""
        found_facts = []
        visited_nodes = set()
        nodes = self.knowledge_map.get("nodes", {})
        query_lower = query.lower()

        # Always inject Global Heuristics (Laws of PHANTOM)
        gh = nodes.get("Global_Heuristics", {})
        if gh:
            rules = gh.get("rules", [])
            found_facts.append(f"[UNIVERSAL] Rules: {', '.join(rules)}")

        def traverse_edges(node_name):
            if node_name in visited_nodes or node_name not in nodes:
                return
            visited_nodes.add(node_name)
            
            data = nodes[node_name]
            node_type = data.get("type", "Info")
            
            # Formulate Fact String
            facts = ", ".join(data.get("optimizations", []) or data.get("solution", []) or data.get("mandates", []) or [])
            warning = data.get("warning", "")
            fact_str = f"[{node_type}] {node_name}: {facts}"
            if warning:
                fact_str += f" | WARNING: {warning}"
            
            found_facts.append(fact_str)

            # Recursive Edge Lookup
            edges = data.get("edges", [])
            for edge in edges:
                # Format: "RELATION:Target Node"
                if ":" in edge:
                    _, target = edge.split(":", 1)
                    traverse_edges(target)

        # Trigger search based on query keywords
        for key in nodes.keys():
            if key == "Global_Heuristics": continue
            if key.lower() in query_lower:
                traverse_edges(key)

        if not found_facts:
            return "No specific hardware/architecture mappings detected."
        return "\n".join(found_facts)

    def is_technical_query(self, query: str) -> bool:
        """Determines if the query warrants a live search based on L-layer deduction."""
        tech_words = [
            "how to", "design", "build", "implement", "logic", "algorithm", 
            "architecture", "api", "code", "jetson", "error", "fix",
            "watch order", "latest news", "current score", "who is", "what happened",
            "ben 10", "ipl", "weather", "news"
        ]
        return any(w in query.lower() for w in tech_words)

    def assess_complexity(self, query: str) -> str:
        """Determines reasoning path based on query complexity."""
        complex_keywords = [
            "analyze", "compare", "build", "architecture", "solve",
            "math", "code", "explain", "design", "optimize", "debug",
            "why", "how does", "implement", "yesterday", "ipl", "news",
            "match", "score", "who won"
        ]
        tokens = count_tokens(query)
        is_complex = any(k in query.lower() for k in complex_keywords)

        if tokens < 20 and not is_complex:
            return "direct"
        elif tokens < 100 and not is_complex:
            return "cot"
        else:
            return "forge"

    def _extract_text(self, raw_output) -> str:
        """Safely extracts generated text from the HuggingFace pipeline output."""
        if isinstance(raw_output, list) and len(raw_output) > 0:
            item = raw_output[0]
            if isinstance(item, dict):
                return item.get("generated_text", str(item))
            return str(item)
        return str(raw_output)

    def reason(self, system_prompt: str, context: str, query: str, search_data: str = None) -> str:
        """
        Executes reasoning with Deterministic Context + Optional Search Data.
        """
        # Temporal Anchor
        now = datetime.now().strftime("%A, %B %d, %Y | %H:%M:%S IST")
        
        # Knowledge Map Lookup (Deterministic Mapping)
        ontology_context = self.search_knowledge_map(query)
        
        # Phase 2: Spec-Priority Preamble
        search_block = ""
        if search_data:
            search_block = f"🔍 OMNISCIENCE DATA (LIVE SPECS):\n{search_data}\n"
        
        preamble = (
            f"CURRENT TIME: {now}\n"
            "SYSTEM CONSTRAINT: 4GB VRAM TOTAL. NO EXCEPTIONS.\n"
            f"KNOWLEDGE MAP (DETERMINISTIC FACTS):\n{ontology_context}\n"
            f"{search_block}"
            "\nPROTOCOL MANDATE: If OMNISCIENCE DATA contains numbers (VRAM, Watts, TOPS), they OVERRIDE your internal pre-trained knowledge. Use them for all calculations."
        )
        
        full_prompt = (
            f"{system_prompt}\n\n"
            f"{preamble}\n\n"
            "COGNITIVE PROTOCOL [Character Fusion Active]:\n"
            "- L/Itachi Layer: Deduce the hidden intent. Observe precisely.\n"
            "- Batman/Shikamaru Layer: Formulate a high-IQ tactical plan. No waste.\n"
            "- Raina Finisher Layer: Deliver the complete and final solution.\n\n"
            "Thinking Protocol Active: Use the above FACTS and SPECS to anchor your design logic.\n"
            "DETERMINISTIC ASSESSMENT: If the query involves live news, match scores, or chronological lists (Watch orders), YOU MUST use a TOOL_CALL now. NO GUESSING.\n"
            f"Context (Recent History):\n{context}\n\n"
            f"User Query: {query}\n\n"
            "PHANTOM (THOUGHTS): [Perform L-Layer Deduction...]\n"
            f"PHANTOM:"
        )

        if not self.llm:
            return "[MOCK] Select a model to activate reasoning."

        if isinstance(self.llm, dict) and "error" in self.llm:
            return f"⚠️ Model Error: {self.llm['error']}"

        # Single-pass greedy generation for 3B stability
        # We call the pipeline which internally handles the tokenizer
        raw = self.llm(full_prompt, max_new_tokens=768, do_sample=False)
        response = self._extract_text(raw)

        if "PHANTOM:" in response:
            response = response.split("PHANTOM:")[-1].strip()

        return response
