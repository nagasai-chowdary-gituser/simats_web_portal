import os
import google.generativeai as genai


# -------- INIT GEMINI CLIENT --------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not set. Use: setx GEMINI_API_KEY \"your-key\"")

client = genai.Client(api_key=api_key)

MODEL_NAME = "models/gemini-2.0-flash"   # from your models list


def generate_ai_content(title: str) -> dict:
    """
    Generates full SIMATS-style capstone content.
    Returns a dict whose KEYS must match your TOC_STRUCTURE in create_ai_docx:
        'Abstract', 'Chapter 1', ..., 'Chapter 6', 'References', 'Appendices'
    """

    # 🔹 IMPORTANT:
    # We ask for ~3–4 Word pages per chapter (≈ 700-750 words).
    # With 6 chapters + abstract + refs + appendices → ~30–32 pages total.

    prompts = {
        "Abstract": f"""
You are writing an ABSTRACT for a SIMATS Engineering capstone report.

Project Title: "{title}"

Write around 250–300 words.
Cover: problem context, objective, approach, key results, impact.
Use formal academic English, single continuous paragraph. Do NOT add headings.
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
""",

        "Appendices": f"""
Write an APPENDICES section description for the capstone titled "{title}".

Do NOT include actual tables or code.
Instead, describe what each appendix would contain, for example:

Appendix A – Dataset description
Appendix B – Sample Screenshots of the Application
Appendix C – Core Algorithm Pseudocode
Appendix D – Additional Graphs and Charts

Write in paragraph form, 200-250 words total, formal academic tone.
"""
"""important:- 
              1.Dont Give This Matter in Any Chapter :- Here's a comprehensive
              draft of Chapter 2 for your capstone project, adhering to your specified 
              structure and requirements
              
              """
    }

    results = {}

    for section_key, prompt in prompts.items():
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        # google.genai returns an object with .text
        results[section_key] = (response.text or "").strip()

    return results