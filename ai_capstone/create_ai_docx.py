import re
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ------------------- FONT + STYLE HELPERS ------------------------

def set_style(paragraph, *, bold=False, align="justify", size=12):
    """Apply Times New Roman formatting."""
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run.font.size = Pt(size)
        run.bold = bold

    if align == "center":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    paragraph.paragraph_format.line_spacing = 1.5


# ------------------- CLEAN AI TEXT ------------------------

def clean_text(text: str):
    text = re.sub(r"#+ ", "", text)  # remove ##, ###, ####
    text = text.replace("*", "")     # remove bullets
    return text.strip()


# ------------------- TABLE OF CONTENTS ------------------------

def extract_subheadings(content):
    """Extract headings like 1.1 Something"""
    subs = []
    for line in content.split("\n"):
        line = line.strip()
        if re.match(r"^\d+\.\d+\s", line):
            subs.append(line)
    return subs


def insert_table_of_contents(doc, sections):
    """Create SIMATS-style Table of Contents."""

    # TITLE
    title = doc.add_paragraph("TABLE OF CONTENTS")
    for r in title.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(16)
        r.bold = True
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    # TABLE
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"

    headers = ["S.No.", "Chapter", "Topics", "Page No."]
    hdr_cells = table.rows[0].cells

    for i, h in enumerate(headers):
        p = hdr_cells[i].paragraphs[0]
        run = p.add_run(h)
        run.font.name = "Times New Roman"
        run.font.size = Pt(8)
        run.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # CONTENT
    sno = 1
    for chapter_title, content in sections.items():

        subs = extract_subheadings(content)
        topics_text = "\n".join(subs) if subs else "—"

        row = table.add_row().cells

        # S.No
        p = row[0].paragraphs[0]
        r = p.add_run(str(sno))
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Chapter Name
        chapter_clean = chapter_title.split(":")[0]  # "Chapter 1"
        p = row[1].paragraphs[0]
        r = p.add_run(chapter_clean)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        r.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Topics
        p = row[2].paragraphs[0]
        r = p.add_run(topics_text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Page Numbers (Static)
        p = row[3].paragraphs[0]
        r = p.add_run("")  # You can fill this later
        r.font.name = "Times New Roman"
        r.font.size = Pt(8)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        sno += 1

    # TABLE KEEP TOGETHER
    for row in table.rows:
        tr = row._tr
        trPr = tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        trPr.append(cant_split)


# ------------------- DOCX BUILDER ------------------------

def create_ai_docx(sections: dict, output_path: str):
    doc = Document()

    insert_table_of_contents(doc, sections)

    # Add each chapter
    for section_title, content in sections.items():

        # MAIN HEADING
        heading = doc.add_paragraph(section_title)
        set_style(heading, bold=True, size=16, align="center")

        text = clean_text(content)
        for line in text.split("\n"):
            if not line.strip():
                continue

            if re.match(r"^\d+\.\d+\s", line):
                p = doc.add_paragraph(line)
                set_style(p, bold=True, size=12, align="left")
            else:
                p = doc.add_paragraph(line)
                set_style(p, bold=False, size=12, align="justify")

        doc.add_page_break()

    doc.save(output_path)
