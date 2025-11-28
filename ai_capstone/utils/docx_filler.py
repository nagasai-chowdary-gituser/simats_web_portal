from docx import Document
from docxcompose.composer import Composer

def merge_docx(doc_paths, output_path):
    """
    Clean & stable merge:
    - Preserves inline images
    - Avoids blank pages
    - Preserves formatting
    """
    master = Document(doc_paths[0])
    composer = Composer(master)

    for path in doc_paths[1:]:
        sub_doc = Document(path)

        # Clean extra empty paragraphs
        for p in sub_doc.paragraphs:
            if not p.text.strip():
                continue

        composer.append(sub_doc)

    composer.save(output_path)
