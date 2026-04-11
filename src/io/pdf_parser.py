import fitz  # PyMuPDF
import os
from typing import Optional

def extract_text_from_pdf(filepath: str) -> Optional[str]:
    """
    Extracts text from a given PDF file.

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
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {filepath}: {str(e)}")
        return None
