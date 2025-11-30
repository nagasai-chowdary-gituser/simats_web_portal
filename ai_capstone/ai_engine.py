import os
import google.generativeai as genai   # ✔ Works on Render & Local

# -------- INIT GEMINI CLIENT --------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=api_key)

MODEL_NAME = "gemini-2.0-flash"

# --------------------------
# SAFE GENERATION FUNCTION
# --------------------------
def safe_generate(model, prompt):
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.55,
                "max_output_tokens": 2000,  # 🔥 prevents freezing
            }
        )
        return (response.text or "").strip()

    except Exception as e:
        print("GENERATION ERROR:", e)
        return "⚠ AI generation failed due to limits. Please regenerate."


def generate_ai_content(title: str) -> dict:
    """
    Generates full SIMATS-style capstone content.
    Output matches DOCX filling structure.
    """

    prompts = {
        "Abstract": f"""
Write a 250–300 word academic ABSTRACT for the SIMATS capstone titled "{title}".
Use formal engineering language.
Single paragraph.
Do NOT add headings.
""",

        "Chapter 1": f"""
Write CHAPTER 1: INTRODUCTION for the capstone titled "{title}".
Length: 700–800 words.
Use EXACT subheadings:
1.1 Background Information
1.2 Problem Definition
1.3 Objectives of the Study
1.4 Scope of the Project
1.5 Methodology Overview
Under each heading, write 2–4 long academic paragraphs.
No bullet points.
""",

        "Chapter 2": f"""
Write CHAPTER 2: PROBLEM ANALYSIS AND REVIEW for "{title}".
Length: 700–800 words.
Use EXACT subheadings:
2.1 Problem Analysis
2.2 Evidence and Motivation
2.3 Stakeholder Requirements
2.4 Challenges Identified
2.5 Supporting Research and Existing Solutions
2.6 Summary
Write 2–3 detailed paragraphs under each.
No bullet points.
""",

        "Chapter 3": f"""
Write CHAPTER 3: SYSTEM DESIGN AND ARCHITECTURE for "{title}".
Length: 700–800 words.
Subheadings:
3.1 Overall System Design
3.2 Architecture Overview
3.3 Tools and Technologies Used
3.4 Data Flow Description
3.5 Functional Modules
3.6 Summary
Write 2–3 strong engineering paragraphs each.
""",

        "Chapter 4": f"""
Write CHAPTER 4: IMPLEMENTATION AND RESULTS for "{title}".
Length: 700–800 words.
Subheadings:
4.1 Implementation Details
4.2 Algorithms and Techniques Used
4.3 System Workflow During Execution
4.4 Experimental Setup and Test Cases
4.5 Performance Evaluation and Discussion
4.6 Summary
2–3 paragraphs under each.
""",

        "Chapter 5": f"""
Write CHAPTER 5: LEARNING, REFLECTION AND PROFESSIONAL ETHICS for "{title}".
Length: 700–800 words.
Subheadings:
5.1 Key Learning Outcomes
5.2 Technical and Problem-Solving Skills Gained
5.3 Teamwork, Collaboration and Communication
5.4 Application of Engineering Standards and Ethics
5.5 Industry Exposure and Real-World Relevance
5.6 Summary
2–3 reflective paragraphs under each.
""",

        "Chapter 6": f"""
Write CHAPTER 6: CONCLUSION AND FUTURE SCOPE for "{title}".
Length: 550–600 words.
Subheadings:
6.1 Summary of the Work
6.2 Major Findings and Contributions
6.3 Impact and Significance of the Project
6.4 Limitations of the Study
6.5 Future Scope and Enhancements
6.6 Conclusion
Write 1–2 clear paragraphs under each.
""",

        "References": f"""
Generate 6–8 IEEE-style references for "{title}".
One reference per line.
Use generic but realistic citations.
Number them [1], [2], [3], ...
""",

        "Appendices": f"""
Write 200–250 words describing the appendices for "{title}".
Do NOT include tables or code.
Just describe:
Appendix A – Dataset description
Appendix B – Sample Screenshots
Appendix C – Algorithm Pseudocode
Appendix D – Graphs and Charts
"""
    }

    results = {}

    model = genai.GenerativeModel(MODEL_NAME)

    # Generate each section individually
    for key, prompt in prompts.items():
        print(f"🟦 Generating: {key} ...")
        results[key] = safe_generate(model, prompt)
        print(f"🟩 Done: {key}")

    return results