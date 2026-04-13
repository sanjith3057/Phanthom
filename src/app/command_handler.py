import re
from rate_limiter import RateLimiter
from tools.pdf_tool import create_pdf
from tools.docx_tool import create_docx
from web_search import search_perplexica, search_google


class JarvisCommandHandler:
    """
    Handles exact-match dot-commands. 
    Enhanced with fuzzy regex to handle missing spaces (e.g., .createpdf).
    """
    def __init__(self):
        self.rate_limiter = RateLimiter()

    def process_command(self, user_input: str) -> str | None:
        text = user_input.strip()
        if not text.startswith("."):
            return None

        # .status — system pulse check
        if text.startswith(".status"):
            import torch
            import os
            from utils import get_project_root
            gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU Mode"
            
            # Diagnostics
            tools_status = []
            try: import fpdf; tools_status.append("PDF: OK")
            except: tools_status.append("PDF: FAIL")
            
            try: import docx; tools_status.append("DOCX: OK")
            except: tools_status.append("DOCX: FAIL")
                
            try: import googlesearch; tools_status.append("Search: OK")
            except: tools_status.append("Search: FAIL")
            
            # Check write perms
            out_dir = os.path.join(get_project_root(), "outputs", "files")
            os.makedirs(out_dir, exist_ok=True)
            can_write = os.access(out_dir, os.W_OK)
            fs_status = "FS: Writable" if can_write else "FS: Read-Only"
            
            status_msg = (
                f"**[STATUS]** ONLINE | **[USER]** Sanjith . G | **[GPU]** {gpu}\n\n"
                f"**[DIAGNOSTICS]** {', '.join(tools_status)} | {fs_status}"
            )
            return status_msg

        # .rest — cooldown check
        if text.startswith(".rest"):
            is_allowed, rem = self.rate_limiter.check_cooldown()
            if is_allowed:
                return "Systems nominal. Cooldown satisfied. Ready for input, Commander."
            else:
                return f"Calibrating systems. Time remaining: {rem}s."

        # .create <pdf|docx> <content> — Handles .createpdf or .create pdf
        create_match = re.match(r"\.create\s?(pdf|docx)\s+(.*)", text, re.IGNORECASE)
        if create_match:
            doc_type = create_match.group(1).lower()
            content = create_match.group(2).strip()
            title = f"PHANTOM Output — {content[:20]}"
            if doc_type == "pdf":
                filepath = create_pdf(title, content)
                return f"✅ PDF compiled for Sanjith: `{filepath}`"
            elif doc_type == "docx":
                filepath = create_docx(title, content)
                return f"✅ Document compiled: `{filepath}`"

        # .search <google|perplexica> <query> — Handles .searchgoogle or .search google
        search_match = re.match(r"\.search\s?(google|perplexica)\s+(.*)", text, re.IGNORECASE)
        if search_match:
            engine = search_match.group(1).lower()
            query = search_match.group(2).strip()
            if engine == "perplexica":
                return search_perplexica(query)
            elif engine == "google":
                return search_google(query)

        return "Unknown command or syntax error. Commander, try `.status` or `.create pdf <text>`."
