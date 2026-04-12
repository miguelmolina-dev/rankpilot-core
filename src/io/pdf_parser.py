import fitz  # PyMuPDF
import os
from typing import Optional

def _clean_table_text(text: str) -> str:
    """Helper to clean text for markdown tables"""
    if not text:
        return ""
    # Replace newlines and pipes with spaces to not break markdown tables
    return str(text).replace("\n", " ").replace("|", " ").strip()

def extract_text_from_pdf(filepath: str) -> Optional[str]:
    """
    Extracts text from a given PDF file, including rendering tables as markdown.

    Args:
        filepath (str): The path to the PDF file.

    Returns:
        Optional[str]: The extracted text, or None if the file cannot be read.
    """
    if not os.path.exists(filepath):
        print(f"Error: PDF file not found at {filepath}")
        return None

    try:
        doc = fitz.open(filepath)
        text_blocks = []
        for page in doc:
            # Extract standard text layout
            page_text = page.get_text()
            if page_text:
                text_blocks.append(page_text)

            # Extract tables if any exist
            tabs = page.find_tables()
            if tabs and tabs.tables:
                text_blocks.append(f"\n--- Tables from Page {page.number + 1} ---")
                for tab in tabs.tables:
                    # extract table to a list of lists of strings
                    rows = tab.extract()
                    if not rows:
                        continue

                    # Build markdown table string
                    table_md = []
                    for i, row in enumerate(rows):
                        cleaned_row = [_clean_table_text(cell) for cell in row]
                        table_md.append("| " + " | ".join(cleaned_row) + " |")
                        # Add markdown header separator after first row
                        if i == 0:
                            header_sep = ["---"] * len(row)
                            table_md.append("| " + " | ".join(header_sep) + " |")

                    text_blocks.append("\n".join(table_md))
                    text_blocks.append("\n") # spacing

        return "\n".join(text_blocks)
    except Exception as e:
        print(f"Error extracting text from PDF {filepath}: {str(e)}")
        return None
