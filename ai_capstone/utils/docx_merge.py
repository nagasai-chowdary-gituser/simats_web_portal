from docxcompose.composer import Composer
from docx import Document

def merge_docx(docs, output_path):
    master = Document(docs[0])
    composer = Composer(master)

    for doc_path in docs[1:]:
        sub = Document(doc_path)
        composer.append(sub)   # this preserves images, headers, footers

    composer.save(output_path)
