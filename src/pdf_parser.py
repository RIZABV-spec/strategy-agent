"""
pdf_parser.py — Extract text from annual report PDFs.
Uses pdfplumber for reliable text extraction from corporate filings.
"""

import pdfplumber


def extract_text(pdf_path: str, max_pages: int = 120) -> str:
    """
    Extract text from a PDF file, page by page.
    
    Args:
        pdf_path: Path to the PDF file
        max_pages: Cap to avoid blowing up token limits (most 10-Ks are 80-150 pages)
    
    Returns:
        Combined text string with page markers
    """
    pages_text = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total = min(len(pdf.pages), max_pages)
        for i, page in enumerate(pdf.pages[:total]):
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(f"--- PAGE {i+1} ---\n{text}")
    
    full_text = "\n\n".join(pages_text)
    return full_text


def chunk_text(full_text: str, max_chars: int = 90_000) -> list[str]:
    """
    Split extracted text into chunks that fit within Claude's context window.
    90K chars ≈ ~25K tokens, leaving room for the prompt + response.
    
    For most annual reports (80-150 pages), you'll get 1-3 chunks.
    """
    if len(full_text) <= max_chars:
        return [full_text]
    
    chunks = []
    current = ""
    
    # Split on page markers to keep pages intact
    sections = full_text.split("--- PAGE ")
    
    for section in sections:
        candidate = current + "--- PAGE " + section if current else section
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = "--- PAGE " + section
        else:
            current = candidate
    
    if current:
        chunks.append(current)
    
    return chunks


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = extract_text(sys.argv[1])
        print(f"Extracted {len(text):,} characters from {sys.argv[1]}")
        print(f"Would split into {len(chunk_text(text))} chunk(s)")
    else:
        print("Usage: python pdf_parser.py <path_to_pdf>")
