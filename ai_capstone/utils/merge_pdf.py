from docxcompose.composer import Composer
from docx import Document

def merge_docx(doc_paths, output_path):
    master = Document(doc_paths[0])
    composer = Composer(master)

    for doc in doc_paths[1:]:
        composer.append(Document(doc))

    composer.save(output_path)
