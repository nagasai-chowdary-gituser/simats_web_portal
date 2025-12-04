import os
import re
from groq import Groq  # ✔ USING GROQ NOW

# -------- INIT GROQ CLIENT --------
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY not set. Use: setx GROQ_API_KEY \"your-key\"")

client = Groq(api_key=api_key)

MODEL_NAME = "openai/gpt-oss-20b"   # ✔ BEST MODEL IN GROQ

##MODEL_NAME = "mixtral-8x7b-32768"




def clean_auto_headings(text: str) -> str:
    """
    Removes unwanted headings, fixes ALL CAPS text,
    keeps Appendix A/B/C/D and marks them for bold formatting.
    """

    forbidden_patterns = [
        r"^INTRODUCTION[\s\-\–\—\:\.\(\[].*$",
        r"^APPENDICES[\s\-\–\—\:\.\(\[].*$",
        r"^APPENDIX\.$",        # exact APPENDIX.
        r"^APPENDIX:$",         # exact APPENDIX:
        r"^APPENDICES:.*$",
        r"^ABSTRACT[\s\-\–\—\:\.\(\[].*$",
    ]

    lines = text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()

        # 1) KEEP REFERENCES
        if stripped.startswith("[") and "]" in stripped[:5]:
            cleaned.append(line)
            continue

        # 2) KEEP Appendix A/B/C/D AND MARK FOR BOLD
        if re.match(r"^Appendix\s+[A-D]\b.*", stripped, re.IGNORECASE):
            cleaned.append(f"@@BOLD@@{stripped}@@END@@")
            continue

        # 3) REMOVE forbidden headings
        if any(re.match(p, stripped, re.IGNORECASE) for p in forbidden_patterns):
            continue

        # 4) FIX ALL CAPS LONG PARAGRAPHS
        if stripped.isupper() and len(stripped.split()) > 6:
            cleaned.append(stripped.capitalize())
            continue

        cleaned.append(line)

    return "\n".join(cleaned).strip()





def generate_ai_content(title: str) -> dict:
    """
    Generates full SIMATS-style capstone content.
    Returns a dict whose KEYS match your TOC_STRUCTURE in create_ai_docx:
        'Abstract', 'Chapter 1', ..., 'Chapter 6', 'References', 'Appendices'
    """

    # ⭐ ALL PROMPTS EXACTLY AS YOU GAVE — NOT A SINGLE WORD CHANGED
    prompts = {
        "Abstract": f"""
You are writing an ABSTRACT for a SIMATS Engineering capstone report.

STRICT RULES:
• Do NOT add any heading like "Abstract", "Introduction", or anything similar.
• Do NOT use bold text.
• Do NOT start with any title or heading.
• The output must be ONLY a single plain paragraph of text.

Project Title: "{title}"

Write around 250–300 words.
Cover: problem context, objective, approach, key results, impact.
Use formal academic English, single continuous paragraph. Do NOT add headings.

Ensure the abstract is rich and detailed enough to fill nearly 1 full Word page.

""",

        "Chapter 1": f"""
Write CHAPTER 1: INTRODUCTION for the capstone project titled "{title}".

Target length: around 3–4 Word pages (roughly 700-800 words).

Structure the content with these numbered subheadings, EXACTLY in this format:

1.1 Background Information
1.2 Problem Definition
1.3 Objectives of the Study
1.4 Scope of the Project
1.5 Methodology Overview

Under each subheading, write 2–4 long paragraphs in formal engineering report style.
Do NOT use bullet points or numbered lists inside the paragraphs.
Just plain paragraphs under each subheading.

Ensure the chapter is written in high detail and long enough to produce 5–6 Word pages (approximately 1200–1500 words).

""",

        "Chapter 2": f"""
Write CHAPTER 2: PROBLEM ANALYSIS AND REVIEW for the capstone titled "{title}".

Target length: around 3–4 Word pages (roughly 700-800 words).

Use EXACTLY these subheadings:

2.1 Problem Analysis
2.2 Evidence and Motivation
2.3 Stakeholder Requirements
2.4 Challenges Identified
2.5 Supporting Research and Existing Solutions
2.6 Summary

For each subheading, write 2–3 detailed academic paragraphs.
No bullet points. Only paragraphs.

Ensure the chapter is written in high detail and long enough to produce 5–6 Word pages (approximately 1200–1500 words).

""",

        "Chapter 3": f"""
Write CHAPTER 3: SYSTEM DESIGN AND ARCHITECTURE for the capstone titled "{title}".

Target length: around 3 Word pages (roughly 700-800 words).

Use EXACTLY these subheadings:

3.1 Overall System Design
3.2 Architecture Overview
3.3 Tools and Technologies Used
3.4 Data Flow Description
3.5 Functional Modules
3.6 Summary

For each subheading, write 2–3 paragraphs.
Explain clearly as if for an engineering capstone report.
No bullet lists.

Ensure the chapter is written in high detail and long enough to produce 5–6 Word pages (approximately 1200–1500 words).

""",

        "Chapter 4": f"""
Write CHAPTER 4: IMPLEMENTATION AND RESULTS for the capstone titled "{title}".

Target length: around 3 Word pages (roughly 700-800 words).

Use EXACTLY these subheadings:

4.1 Implementation Details
4.2 Algorithms and Techniques Used
4.3 System Workflow During Execution
4.4 Experimental Setup and Test Cases
4.5 Performance Evaluation and Discussion
4.6 Summary

Under each subheading, write 2–3 detailed paragraphs.
Focus on technical clarity. No bullet points.

Ensure the chapter is written in high detail and long enough to produce 5–6 Word pages (approximately 1200–1500 words).

""",

        "Chapter 5": f"""
Write CHAPTER 5: LEARNING, REFLECTION AND PROFESSIONAL ETHICS for the capstone titled "{title}".

Target length: around 3 Word pages (roughly 700-800 words).

Use EXACTLY these subheadings:

5.1 Key Learning Outcomes
5.2 Technical and Problem-Solving Skills Gained
5.3 Teamwork, Collaboration and Communication
5.4 Application of Engineering Standards and Ethics
5.5 Industry Exposure and Real-World Relevance
5.6 Summary

Write 2–3 reflective academic paragraphs under each subheading.
No bullet lists.

Ensure the chapter is written in high detail and long enough to produce 5–6 Word pages (approximately 1200–1500 words).

""",

        "Chapter 6": f"""
Write CHAPTER 6: CONCLUSION AND FUTURE SCOPE for the capstone titled "{title}".

Target length: around 2–3 Word pages (roughly 550-600 words).

Use EXACTLY these subheadings:

6.1 Summary of the Work
6.2 Major Findings and Contributions
6.3 Impact and Significance of the Project
6.4 Limitations of the Study
6.5 Future Scope and Enhancements
6.6 Conclusion

Each subheading should have 1–2 rich paragraphs in formal report style.
No bullet points.

Ensure the chapter is written in high detail and long enough to produce 5–6 Word pages (approximately 1200–1500 words).

""",

        "References": f"""
Generate 6-8 references for the capstone titled "{title}".

Use a mix of:
- journal articles
- conference papers
- websites
- official reports
- standards / documentation (if relevant)

Follow a simple IEEE-like style, ONE reference per line, such as:
[1] Author Names, "Paper Title," Journal/Conference, Year.
[2] Organization, "Webpage Title," Website, Year, URL: https://...

IMPORTANT:
• Do NOT invent obviously fake organizations.
• Use generic but realistic-sounding citations.
• Number the references [1], [2], [3], ...

Ensure references list fills nearly 1 full Word page.

""",

        "Appendices": f"""
Write an APPENDICES section description for the capstone titled "{title}".

STRICT RULES:
• Do NOT add ANY heading such as "Appendices", "Appendices Introduction", or anything similar.
• Do NOT number anything.
• Do NOT bold anything except side headings.

Do NOT include actual tables or code.
Instead, describe what each appendix would contain, for example:

Appendix A – Dataset description
Appendix B – Sample Screenshots of the Application
Appendix C – Core Algorithm Pseudocode
Appendix D – Additional Graphs and Charts

Write in paragraph form, 200-250 words total, formal academic tone.

Ensure the appendix description fills at least 1 full Word page.

"""
    }

    results = {}

    # ⭐ NEW GROQ GENERATION LOOP
    for section_key, prompt in prompts.items():
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        
        raw_text = response.choices[0].message.content
        cleaned_text = clean_auto_headings(raw_text)
        results[section_key] = cleaned_text


    return results
