from docx import Document

def merge_docx(docx_list, output_path):
    final_doc = Document(docx_list[0])  # first page

    for file in docx_list[1:]:
        temp = Document(file)
        for element in temp.element.body:
            final_doc.element.body.append(element)

    final_doc.save(output_path)
