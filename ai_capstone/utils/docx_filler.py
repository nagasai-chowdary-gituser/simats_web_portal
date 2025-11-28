from docx import Document

def merge_docx(docx_list, output_path):
    """
    Merge multiple DOCX files into a single final DOCX.
    Each DOCX file represents one fixed page or an AI-generated section.
    """

    # Start with the first document
    final_doc = Document(docx_list[0])

    # Append remaining DOCX files
    for file in docx_list[1:]:
        temp_doc = Document(file)
        for element in temp_doc.element.body:
            final_doc.element.body.append(element)

    # Save final merged DOCX
    final_doc.save(output_path)
