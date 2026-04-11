import os
import docx

def assemble_submission(template_path: str, output_dir: str, submission_data: dict) -> str:
    """
    Reads the given template docx, injects JSON results from submission_data,
    and saves the new document to the output_dir.

    Args:
        template_path (str): The path to the original docx template.
        output_dir (str): The path to the directory where the new file should be saved.
        submission_data (dict): The data extracted by the system to inject.

    Returns:
        str: The path to the newly generated docx file.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Load the template
    doc = docx.Document(template_path)

    # Map identity data
    identity = submission_data.get('identity', {})
    if isinstance(identity, dict):
        if 'firm_name' in identity and len(doc.tables) > 1:
            doc.tables[1].rows[0].cells[0].text = str(identity['firm_name'])
        if 'country' in identity and len(doc.tables) > 2:
            doc.tables[2].rows[0].cells[0].text = str(identity['country'])
        if 'practice_area' in identity and len(doc.tables) > 3:
            doc.tables[3].rows[0].cells[0].text = str(identity['practice_area'])

    # Map department info
    department = submission_data.get('department_info')
    if department:
        if len(doc.tables) > 5:
            doc.tables[5].rows[0].cells[0].text = str(department)

    # Map narratives
    narratives = submission_data.get('narratives')
    if narratives:
        for i, p in enumerate(doc.paragraphs):
            if "Your practice: what sets your practice apart" in p.text:
                p.insert_paragraph_before(str(narratives))
                break

    # Map clients
    clients = submission_data.get('clients')
    if clients:
        for i, p in enumerate(doc.paragraphs):
            if "Clients: publishable clients" in p.text:
                p.insert_paragraph_before(str(clients))
                break

    # If any other data is present that wasn't mapped specifically, append it.
    # In a full system, you would map all required_fields explicitly.
    mapped_keys = ['identity', 'department_info', 'narratives', 'clients']
    unmapped = {k: v for k, v in submission_data.items() if k not in mapped_keys}

    if unmapped:
        try:
            doc.add_heading('Other Generated Results', level=1)
        except KeyError:
            doc.add_paragraph('Other Generated Results')

        for key, value in unmapped.items():
            try:
                doc.add_heading(str(key).replace('_', ' ').title(), level=2)
            except KeyError:
                doc.add_paragraph(str(key).replace('_', ' ').title())

            if isinstance(value, dict):
                for k, v in value.items():
                    doc.add_paragraph(f"{k}: {v}")
            elif isinstance(value, list):
                for item in value:
                    doc.add_paragraph(f"- {item}")
            else:
                doc.add_paragraph(str(value))

    # Determine the output filename based on the template name
    template_filename = os.path.basename(template_path)
    output_filename = f"filled_{template_filename}"
    output_filepath = os.path.join(output_dir, output_filename)

    # Save the document
    doc.save(output_filepath)

    return output_filepath
