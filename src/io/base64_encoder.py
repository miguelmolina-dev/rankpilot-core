import base64
import os
from typing import Optional

def encode_file_to_base64(filepath: str) -> Optional[str]:
    """
    Reads a file and converts it into a base64 string.
    Returns the base64 string, or None if the file does not exist or an error occurs.
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return None

    try:
        with open(filepath, "rb") as f:
            file_data = f.read()
            return base64.b64encode(file_data).decode("utf-8")
    except Exception as e:
        print(f"Error encoding base64 for file {filepath}: {str(e)}")
        return None
