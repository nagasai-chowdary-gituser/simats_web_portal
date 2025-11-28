from fpdf import FPDF

class CapstonePDF(FPDF):
    def header(self):
        # SIMATS capstone does NOT require headers in the chapters
        pass

    def footer(self):
        # Page number at bottom center
        self.set_y(-15)
        self.set_font("Times", "I", 10)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def generate_ai_pdf(sections: dict, output_path: str):
    """
    Creates a PDF of the AI-generated chapters.
    sections: {"Chapter 1: ...": "content", ...}
    output_path: final path of AI-only PDF
    """
    pdf = CapstonePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(left=20, top=20, right=20)

    for section_title, content in sections.items():
        pdf.add_page()

        # Title of each chapter
        pdf.set_font("Times", "B", 18)
        pdf.multi_cell(0, 10, section_title)
        pdf.ln(4)

        # Chapter body
        pdf.set_font("Times", "", 12)

        # Replace unsupported unicode (FPDF limitation)
        safe_text = content.replace("•", "-").replace("–", "-")

        # Multi-line content
        pdf.multi_cell(0, 7, safe_text)
        pdf.ln(5)

    # Save final PDF
    pdf.output(output_path)
