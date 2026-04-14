import re

def chunk_chambers_submission(text: str) -> dict:
    """
    Splits a Chambers submission document into up to 5 logical chunks: A, B, C, D, and E.
    Dynamically handles missing sections.
    """
    # Regex patterns for each major Chambers section
    patterns = {
        "A": r"(?m)^A\.\s+PRELIMINARY",
        "B": r"(?m)^B\.\s+DEPARTMENT",
        "C": r"(?m)^C\.\s+FEEDBACK",
        "D": r"(?m)^D\.\s+PUBLISHABLE",
        "E": r"(?m)^E\.\s+CONFIDENTIAL"
    }
    
    # 1. Find the starting index of every section that actually exists in the text
    indices = {}
    for section, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            indices[section] = match.start()
            
    chunks = {}
    
    # 2. Sort the found sections based on where they appear in the document
    # Example: [('A', 150), ('B', 1200), ('D', 4500)]
    sorted_sections = sorted(indices.items(), key=lambda item: item[1])
    
    # 3. Slice the text between the found indices
    for i in range(len(sorted_sections)):
        current_section, start_idx = sorted_sections[i]
        
        # If it's the last section found, slice from its start to the very end of the document
        if i == len(sorted_sections) - 1:
            chunks[current_section] = text[start_idx:]
        else:
            # Otherwise, slice up to the start of the next section
            next_section, next_start_idx = sorted_sections[i + 1]
            chunks[current_section] = text[start_idx:next_start_idx]
            
    # Fallback: If the regex didn't find ANY headers, return the whole text so it doesn't crash
    if not chunks:
        chunks["Full"] = text
        
    return chunks