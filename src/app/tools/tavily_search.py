import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class TavilyExecutor:
    """
    Executes deep technical searches using the Tavily API.
    Optimized for technical and coding research for PHANTOM-3B.
    """
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment.")
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, depth: str = "advanced") -> str:
        try:
            print(f"DEBUG: Triggering Tavily Search [{depth}]: {query}")
            response = self.client.search(query=query, search_depth=depth, max_results=5)
            
            if not response.get('results'):
                return "No high-confidence results found via Tavily."

            formatted_results = []
            for result in response['results']:
                title = result.get('title', 'Unknown Title')
                content = result.get('content', '')
                url = result.get('url', '')
                formatted_results.append(f"### {title}\nURL: {url}\n{content}\n")

            return "\n".join(formatted_results)
        except Exception as e:
            return f"⚠️ Tavily Search Error: {str(e)}"
