import os
import time
from fpdf import FPDF
from utils import get_project_root

# Resolve output directory as absolute path from project root
OUTPUT_DIR = os.path.join(get_project_root(), "outputs", "files")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def create_pdf(title: str, text_content: str, filename: str = None) -> str:
    """
    Generates a PDF file containing the provided Title and Text Content.
    Returns the absolute path to the generated PDF.
    """
    ensure_dir(OUTPUT_DIR)

    if not filename:
        timestamp = int(time.time())
        safe_title = "".join([c for c in title if c.isalnum() or c == ' ']).strip().replace(' ', '_')
        filename = f"{safe_title}_{timestamp}.pdf"

    if not filename.endswith('.pdf'):
        filename += '.pdf'

    filepath = os.path.join(OUTPUT_DIR, filename)

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", 'B', size=16)
    safe_title = title.encode('latin-1', errors='replace').decode('latin-1')
    pdf.cell(200, 10, txt=safe_title, ln=True, align='C')
    pdf.ln(10)

    # Body — multi_cell auto-wraps text
    pdf.set_font("Arial", size=12)
    # Encode to latin-1 to avoid FPDF unicode errors
    safe_content = text_content.encode('latin-1', errors='replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_content)

    pdf.output(filepath)
    return os.path.abspath(filepath)


if __name__ == "__main__":
    res = create_pdf("Jarvis Diagnostic", "All systems operate at optimal capacity.")
    print(f"Generated: {res}")
