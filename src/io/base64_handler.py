import base64
import os
from typing import Optional

ALLOWED_EXTENSIONS = {'.docx', '.pdf', '.xlsx'}

def decode_base64_document(b64_string: str, filename: str, output_dir: str = "/tmp") -> Optional[str]:
    """
    Decodes a base64 string into a file.
    Validates that the file has an allowed extension (.docx, .pdf, .xlsx).
    Returns the path to the decoded file, or None if the extension is invalid.
    """
    # Sanitize filename to prevent Path Traversal
    safe_filename = os.path.basename(filename)

    _, ext = os.path.splitext(safe_filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        print(f"Unsupported file extension: {ext}. Allowed: {ALLOWED_EXTENSIONS}")
        return None

    try:
        # Some base64 strings might include the data URI prefix like "data:application/pdf;base64,..."
        if "," in b64_string:
            b64_string = b64_string.split(",", 1)[1]

        file_data = base64.b64decode(b64_string)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, safe_filename)

        with open(output_path, "wb") as f:
            f.write(file_data)

        return output_path
    except Exception as e:
        print(f"Error decoding base64 for file {filename}: {str(e)}")
        return None
