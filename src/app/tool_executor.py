import re
import json
from tools.pdf_tool import create_pdf
from tools.docx_tool import create_docx
from tools.calculator import calculate
from tools.tavily_search import TavilyExecutor
from web_search import search_google, search_perplexica


class ToolExecutor:
    """
    Scans LLM responses for embedded <TOOL_CALL> JSON tags and executes them.
    Phase 1: Formal scan for <TOOL_CALL>...</TOOL_CALL> blocks.
    Phase 2: Fuzzy fallback — detects raw JSON blocks the model hallucinates
             without proper tags (common in 3B-level models).
    Phase 3: Functional fallback — detects NAME(query="...") style hallucinations
    """
    def __init__(self):
        self._tool_pattern = re.compile(r"<TOOL_CALL>(.*?)</TOOL_CALL>", re.DOTALL)
        # Fuzzy fallback: catch raw JSON blocks the model forgot to wrap
        self._json_pattern = re.compile(r"\{[^{}]*\"(tool|query|function_name|command)\"[^{}]*\}", re.DOTALL)
        
        # Phase 3: Functional fallback — detects NAME(query="...") style hallucinations
        self._functional_pattern = re.compile(r"([A-Z_]+)\(\s*query\s*=\s*(['\"])(.*?)\2\s*\)", re.DOTALL)

        # ─── AGGRESSIVE ALIAS MAP ────────────────────────────────────────────────
        # Every hallucinated tool name the 3B model has ever produced,
        # mapped to our actual internal tool names.
        self._aliases = {
            # PDF aliases
            "pdf_creator":           "pdf_tool",
            "pdf_generator":         "pdf_tool",
            "pdf_maker":             "pdf_tool",
            "create_pdf":            "pdf_tool",
            # DOCX aliases
            "docx_creator":          "docx_tool",
            "word_document":         "docx_tool",
            # ─── SEARCH ALIASES (the main hallucination source) ──────────────────
            "search_google":         "search_tavily",  # Upgrade to tavily for "Real AI" feel
            "google_search":         "search_tavily",
            "web_search":            "search_tavily",
            "web_research":          "search_tavily",
            "search":                "search_tavily",
            "internet_search":       "search_tavily",
            "search_web":            "search_tavily",
            "google_cloud_functions":"search_tavily",  # 3B hallucinates GCP
            "openai_chat_completion":"search_tavily",  # 3B hallucinates OpenAI
            "openai_search":         "search_tavily",
            "mlflow_tracking":       "search_tavily",  # 3B hallucinates MLflow
            "docker_container":      "search_tavily",  # 3B hallucinates Docker calls
            "api_call":              "search_tavily",
            "fetch_data":            "search_tavily",
            "get_ipl_winner":        "search_tavily",  # 3B hallucinates function names
            "get_news":              "search_tavily",
            "get_match_results":     "search_tavily",
            "iplay":                 "search_tavily",
            # Math aliases
            "math":                  "calculator",
            "calculate":             "calculator",
            "calc":                  "calculator",
            "tavily_search":         "search_tavily",
            "tavily":                "search_tavily",
            "deep_search":           "search_tavily",
        }

    def detect_and_execute(self, llm_response: str) -> tuple[bool, str]:
        """Phase 1: Formal <TOOL_CALL> detection."""
        match = self._tool_pattern.search(llm_response)
        if match:
            return self._execute_match(llm_response, match)

        # Phase 2: Fuzzy fallback — raw JSON block without tags
        fuzzy_match = self._json_pattern.search(llm_response)
        if fuzzy_match:
            return self._execute_fuzzy(llm_response, fuzzy_match)

        # Phase 3: Functional fallback — model outputted NAME(query="...")
        func_match = self._functional_pattern.search(llm_response)
        if func_match:
            return self._execute_functional(llm_response, func_match)

        return False, llm_response

    def _execute_match(self, llm_response: str, match) -> tuple[bool, str]:
        """Executes a formally tagged <TOOL_CALL> block."""
        try:
            raw_json = match.group(1).strip()
            tool_data = json.loads(raw_json)
            tool_name = tool_data.get("tool", "").lower()
            resolved_tool = self._aliases.get(tool_name, tool_name)
            result_msg = self._dispatch(resolved_tool, tool_data)
            final = (
                llm_response[:match.start()].strip()
                + f"\n\n> **[SYSTEM ACTION]** {result_msg}"
                + llm_response[match.end():].strip()
            )
            return True, final.strip()
        except json.JSONDecodeError:
            return False, llm_response
        except ValueError as ve:
            return True, f"⚠️ Tool Notice: {str(ve)}"
        except Exception as e:
            return True, f"⚠️ Tool Execution Error: {str(e)}"

    def _execute_fuzzy(self, llm_response: str, match) -> tuple[bool, str]:
        """
        Fuzzy fallback: model generated a raw JSON block without TOOL_CALL tags.
        We intercept it, try to extract a query, and force a search.
        """
        try:
            raw_json = match.group(0).strip()
            tool_data = json.loads(raw_json)
            # Try to find a tool name
            tool_name = (
                tool_data.get("tool", "")
                or tool_data.get("function_name", "")
                or tool_data.get("command", "")
            ).lower()
            resolved_tool = self._aliases.get(tool_name, "search_tavily")
            # Try to find a query
            query = (
                tool_data.get("query", "")
                or tool_data.get("input_data", "")
                or tool_data.get("prompt", "")
                or tool_data.get("q", "")
            )
            if not query:
                # No query found — suppress the JSON block, don't execute
                clean = llm_response[:match.start()].strip()
                return True, clean if clean else llm_response
            # Build a normalized tool_data and dispatch
            tool_data["query"] = query
            result_msg = self._dispatch(resolved_tool, tool_data)
            # Replace the raw JSON block with the search result
            final = (
                llm_response[:match.start()].strip()
                + f"\n\n> **[SYSTEM ACTION — Auto-Detected]** {result_msg}"
            )
            return True, final.strip()
        except Exception:
            # Fuzzy failed — just strip the JSON block silently
            clean = llm_response[:match.start()].strip()
            return True, clean if clean else llm_response

    def _execute_functional(self, llm_response: str, match) -> tuple[bool, str]:
        """
        Functional fallback: model generated NAME(query="...") style call.
        """
        try:
            func_name = match.group(1).lower()
            query = match.group(3)
            
            resolved_tool = self._aliases.get(func_name, "search_tavily")
            result_msg = self._dispatch(resolved_tool, {"query": query})
            
            final = (
                llm_response[:match.start()].strip() 
                + f"\n\n> **[SYSTEM ACTION — Functional Logic]** {result_msg}"
            )
            return True, final.strip()
        except Exception:
            return False, llm_response

    def _dispatch(self, tool_name: str, data: dict) -> str:
        """Routes to the correct tool implementation."""
        if tool_name in ["python_function", "code_executor"]:
            return (
                "Code execution is disabled in PHANTOM-3B stable build. "
                "Output calculations as text instead."
            )

        if tool_name == "pdf_tool":
            path = create_pdf(data.get("title", "Document"), data.get("content", ""))
            return f"PDF generated → `{path}`"

        elif tool_name == "docx_tool":
            path = create_docx(data.get("title", "Document"), data.get("content", ""))
            return f"DOCX generated → `{path}`"

        elif tool_name == "search_google":
            result = search_google(data.get("query", ""))
            return f"Search complete:\n{result}"

        elif tool_name == "search_perplexica":
            result = search_perplexica(data.get("query", ""))
            return f"Perplexica:\n{result}"

        elif tool_name == "search_tavily":
            try:
                executor = TavilyExecutor()
                result = executor.search(data.get("query", ""))
                return f"Tavily Deep Research:\n{result}"
            except Exception as e:
                return f"⚠️ Tavily Error: {str(e)}"

        elif tool_name == "calculator":
            # Extract expression from 'query', 'expr', or 'input_data'
            expr = data.get("query") or data.get("expr") or data.get("input_data") or ""
            result = calculate(expr)
            return f"Calculation Result: {result}"

        else:
            raise ValueError(
                f"Unknown tool '{tool_name}'. "
                f"Available: pdf_tool, docx_tool, search_google, search_perplexica."
            )
