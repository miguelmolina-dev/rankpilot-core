import re
from docxtpl import RichText

def parse_markdown_to_richtext(text_string: str) -> RichText:
    """
    Converts a string with **markdown bold** into a docxtpl RichText object.
    """
    if not text_string or not isinstance(text_string, str):
        return text_string # Return as-is if it's not a string

    rt = RichText()
    parts = re.split(r'\*\*(.*?)\*\*', text_string)
    
    for i, part in enumerate(parts):
        if not part:
            continue
            
        if i % 2 == 0:
            rt.add(part)
        else:
            rt.add(part, bold=True)
            
    return rt

def convert_all_markdown_to_richtext(data):
    """
    Recursively scans a dictionary or list and converts any **bold** strings 
    into docxtpl RichText objects in place.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str) and '**' in v:
                data[k] = parse_markdown_to_richtext(v)
            elif isinstance(v, (dict, list)):
                convert_all_markdown_to_richtext(v)
    elif isinstance(data, list):
        for i in range(len(data)):
            if isinstance(data[i], str) and '**' in data[i]:
                data[i] = parse_markdown_to_richtext(data[i])
            elif isinstance(data[i], (dict, list)):
                convert_all_markdown_to_richtext(data[i])