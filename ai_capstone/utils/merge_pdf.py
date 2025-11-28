import os
from PyPDF2 import PdfMerger

def merge_pdfs(pdf_list, output_path):
    """
    pdf_list = list of PDF file paths in correct order
    output_path = final merged PDF
    """
    merger = PdfMerger()

    for pdf in pdf_list:
        if os.path.exists(pdf):
            merger.append(pdf)
        else:
            print(f"[WARNING] PDF not found: {pdf}")

    with open(output_path, "wb") as final_pdf:
        merger.write(final_pdf)

    merger.close()
