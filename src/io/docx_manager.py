import os
import docx
import jinja2
from docxtpl import DocxTemplate

class SilentUndefined(jinja2.Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ''
    __str__ = __unicode__ = _fail_with_undefined_error
    def __getattr__(self, name):
        return self.__class__(name=name)

def extract_text_from_docx(filepath: str) -> str:
    """
    Extracts all text from a given docx file.

    Args:
        filepath (str): The path to the docx file.

    Returns:
        str: The extracted text, or None if the file cannot be read.
    """
    if not os.path.exists(filepath):
        print(f"Error: docx file not found at {filepath}")
        return None

    try:
        doc = docx.Document(filepath)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error extracting text from docx {filepath}: {str(e)}")
        return None

def _convert_booleans_to_yes_no(data):
    """
    Recursively converts boolean values in a dictionary or list
    to 'Yes' or 'No' strings.
    """
    if isinstance(data, dict):
        return {k: _convert_booleans_to_yes_no(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_convert_booleans_to_yes_no(item) for item in data]
    elif isinstance(data, bool):
        return "Yes" if data else "No"
    else:
        return data

def assemble_submission(template_path: str, output_dir: str, submission_data: dict) -> str:
    """
    Reads the given template docx, uses docxtpl to inject JSON results from submission_data
    using Jinja tags, and saves the new document to the output_dir.

    Args:
        template_path (str): The path to the original docx template.
        output_dir (str): The path to the directory where the new file should be saved.
        submission_data (dict): The data extracted by the system to inject.

    Returns:
        str: The path to the newly generated docx file.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Split lists into publishable/non-publishable
    if 'clients' in submission_data and isinstance(submission_data['clients'], list):
        publishable_clients = []
        non_publishable_clients = []
        for client in submission_data['clients']:
            if client.get('is_publishable', False):
                publishable_clients.append(client)
            else:
                non_publishable_clients.append(client)
        submission_data['publishable_clients'] = publishable_clients
        submission_data['non_publishable_clients'] = non_publishable_clients

    if 'matters' in submission_data and isinstance(submission_data['matters'], list):
        publishable_matters = []
        non_publishable_matters = []
        for matter in submission_data['matters']:
            if matter.get('is_publishable', False):
                publishable_matters.append(matter)
            else:
                non_publishable_matters.append(matter)
        submission_data['publishable_matters'] = publishable_matters
        submission_data['non_publishable_matters'] = non_publishable_matters

    # 2. Convert all booleans to Yes/No strings
    context = _convert_booleans_to_yes_no(submission_data)

    # 3. Load the template with docxtpl
    doc = DocxTemplate(template_path)

    # 4. Render the template
    # Use a custom Jinja environment with SilentUndefined to handle out-of-bounds indices
    jinja_env = jinja2.Environment(undefined=SilentUndefined)
    doc.render(context, jinja_env=jinja_env)

    # Determine the output filename based on the template name
    template_filename = os.path.basename(template_path)
    output_filename = f"filled_{template_filename}"
    output_filepath = os.path.join(output_dir, output_filename)

    # Save the document
    doc.save(output_filepath)

    return output_filepath
