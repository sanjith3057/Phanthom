import os
import requests
from dotenv import load_dotenv

load_dotenv()

PERPLEXICA_API_URL = os.getenv("PERPLEXICA_API_URL", "http://localhost:3000/api/search")


def search_google(query: str, num_results: int = 2) -> str:
    """
    Performs a Google search using the googlesearch-python library.
    Limited to 2 results to preserve PHANTOM context.
    """
    try:
        from googlesearch import search
        results = []
        for item in search(query, num_results=num_results, advanced=True):
            results.append(
                f"**{item.title}**\n{item.url}\n{item.description}"
            )
        if not results:
            # Fallback to Serper if available
            return search_serper(query)
        return "=== Google Search (Classic) ===\n\n" + "\n\n---\n\n".join(results)
    except ImportError:
        return search_serper(query)
    except Exception:
        return search_serper(query)


def search_serper(query: str, num_results: int = 2) -> str:
    """
    Performs a reliable Google search via Serper.dev API.
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "⚠️ SERPER_API_KEY missing in .env. Falling back to classic search..."
    
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": num_results}
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("organic", []):
                results.append(f"**{item.get('title')}**\n{item.get('link')}\n{item.get('snippet')}")
            if not results:
                return "No Serper results found."
            return "=== Serper Intelligence ===\n\n" + "\n\n---\n\n".join(results)
        return f"⚠️ Serper Search Error [HTTP {response.status_code}]"
    except Exception as e:
        return f"Serper Connection Error: {str(e)}"


def search_perplexica(query: str) -> str:
    """
    Queries a local Perplexica AI search backend via REST API.
    Refined to match the BunsDev/Perplexica API spec.
    """
    try:
        # Load config from env or use defaults
        chat_model = os.getenv("PERPLEXICA_CHAT_MODEL", "gpt-3.5-turbo")
        chat_provider = os.getenv("PERPLEXICA_CHAT_PROVIDER", "openai")
        emb_model = os.getenv("PERPLEXICA_EMB_MODEL", "text-embedding-3-small")
        emb_provider = os.getenv("PERPLEXICA_EMB_PROVIDER", "openai")

        payload = {
            "query": query,
            "focusMode": "web", # academic, news, writing, etc.
            "optimizationMode": "speed",
            "chatModel": {
                "provider": chat_provider,
                "model": chat_model
            },
            "embeddingModel": {
                "provider": emb_provider,
                "model": emb_model
            }
        }
        response = requests.post(PERPLEXICA_API_URL, json=payload, timeout=30)
        # ... logic continues below

        if response.status_code == 200:
            data = response.json()
            answer = data.get("message", "No response content.")
            sources = data.get("sources", [])
            src_text = ""
            if sources:
                src_text = "\n\nSources:\n" + "\n".join(
                    f"- {s.get('metadata', {}).get('title', 'Link')}: {s.get('metadata', {}).get('url', '')}"
                    for s in sources[:2]
                )
            return f"=== Perplexica Intelligence ===\n\n{answer}{src_text}"
        else:
            return (
                f"⚠️ Perplexica Error [HTTP {response.status_code}]: "
                f"Is it running at `{PERPLEXICA_API_URL}`?"
            )
    except requests.exceptions.ConnectionError:
        return f"⚠️ Perplexica not reachable at `{PERPLEXICA_API_URL}`. Start your Perplexica instance first."
    except Exception as e:
        return f"Perplexica Error: {str(e)}"


import re

def extract_technical_specs(text: str) -> str:
    """
    Surgically extracts 'Hard Data' from search results using pattern matching.
    Focuses on VRAM, Watts, TOPS, Clock Speeds, and Memory.
    """
    spec_patterns = [
        r"\b\d+\s?GB\b",              # RAM/VRAM
        r"\b\d+\s?MB\b",              # Cache
        r"\b\d+\s?W\b",               # Power (Watts)
        r"\b\d+\s?TOPS\b",            # AI Performance
        r"\b\d+\.\d+\s?GHz\b",         # Clock Speed
        r"\b\d+\s?MHz\b",             # Clock Speed
        r"\b\d+\s?CUDA\b",            # Core count
        r"\bJetPack\s?\d+\.\d+\b",     # NVIDIA Specific
        r"\bOrin\s?\w+\b"             # Model naming
    ]
    
    specs = set()
    for pattern in spec_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            specs.add(m.strip().upper())
            
    if not specs:
        return ""
        
    return "=== DETECTED TECHNICAL SPECS ===\n" + ", ".join(sorted(list(specs)))


def smart_search(query: str) -> str:
    """
    Attempts Perplexica first (local AI search), 
    then falls back to Serper/Google if Perplexica is unreachable.
    Injects a Technical Spec Block for deterministic accuracy.
    """
    print(f"DEBUG: Attempting Smart Search for: {query}")
    perplexica_result = search_perplexica(query)
    
    if "⚠️ Perplexica not reachable" in perplexica_result or "⚠️ Perplexica Error" in perplexica_result:
        print("DEBUG: Perplexica offline. Falling back to Serper...")
        raw_result = search_serper(query)
    else:
        raw_result = perplexica_result

    # Phase 2: Spec Extraction Pass
    spec_block = extract_technical_specs(raw_result)
    
    if spec_block:
        return f"{spec_block}\n\n{raw_result}"
    return raw_result


if __name__ == "__main__":
    print(smart_search("PHANTOM AI model merging 2026"))
