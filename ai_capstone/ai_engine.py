import os
import google.generativeai as genai  # ✔ CORRECT import


# -------- INIT GEMINI CLIENT --------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not set. Use: setx GEMINI_API_KEY \"your-key\"")

# ✔ NEW way to configure Gemini API
genai.configure(api_key=api_key)

MODEL_NAME = "gemini-1.5-flash"   # ✔ Correct model naming in new SDK


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
...
""",

        # ⭐ I am NOT touching your prompts. They remain EXACTLY as you wrote.
        # ⭐ (I cut them from here for shortness, but in your file keep ALL of them.)
    }

    results = {}

    # ✔ NEW Gemini usage (same behaviour, same result)
    model = genai.GenerativeModel(MODEL_NAME)

    for section_key, prompt in prompts.items():
        response = model.generate_content(prompt)
        results[section_key] = (response.text or "").strip()

    return results
