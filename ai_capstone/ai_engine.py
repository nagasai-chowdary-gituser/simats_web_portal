import os
from google.genai import Client
from dotenv import load_dotenv

# Load ENV variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise Exception("❌ GEMINI_API_KEY not set in environment variables!")

client = Client(api_key=api_key)

MODEL_NAME = "models/gemini-2.5-flash"   # Best model from your list


def generate_ai_content(title: str) -> dict:
    """
    Generates capstone content with controlled size (25–30 pages total).
    """

    MODEL_NAME = "models/gemini-2.5-flash"

    sections_prompt = {
        "Abstract": f"""
Write a concise ABSTRACT for "{title}" within 180–220 words.
Avoid long paragraphs. Use only 2–3 medium paragraphs.
""",

        "Chapter 1: Introduction": f"""
Write Chapter 1 for "{title}".
IMPORTANT RULES:
- Write ONLY 350–450 words total.
- Create EXACTLY 3 subheadings: 1.1, 1.2, 1.3
- Each subheading must be 1 medium paragraph (6–8 lines).
- Do NOT exceed 3 subheadings.
""",

        "Chapter 2: Problem Identification and Analysis": f"""
Write Chapter 2 for "{title}".
RULES:
- Length must be 350–450 words.
- EXACTLY 3 subheadings: 2.1, 2.2, 2.3
- Each section = 1 medium paragraph only.
""",

        "Chapter 3: Literature Review": f"""
Write Chapter 3 for "{title}".
RULES:
- Write 400–500 words (not more).
- EXACTLY 4 subheadings: 3.1, 3.2, 3.3, 3.4
- Each subheading = max 7–9 lines.
""",

        "Chapter 4: System Design": f"""
Write Chapter 4 for "{title}".
RULES:
- 350–450 words only.
- 3 subheadings maximum: 4.1, 4.2, 4.3
- No long paragraphs.
""",

        "Chapter 5: Implementation": f"""
Write Chapter 5 for "{title}".
RULES:
- 350–450 words.
- EXACTLY 3 subheadings: 5.1, 5.2, 5.3
- Each 6–8 lines only.
""",

        "Chapter 6: Results & Evaluation": f"""
Write Chapter 6 for "{title}".
RULES:
- 300–450 words.
- EXACTLY 3 subheadings: 6.1, 6.2, 6.3
- No long essays.
""",

        "Chapter 7: Conclusion & Future Scope": f"""
Write Chapter 7 for "{title}".
RULES:
- 250–350 words total.
- EXACTLY 2 subheadings: 7.1, 7.2
- No extra sections.
""",

        "References": f"""
Generate EXACTLY 10 references for "{title}".
Each reference must be 1 short line.
Avoid numbering.
Use APA/IEEE mixed citations.
""",

        "Appendices": f"""
Write a short placeholder appendix summary (150–200 words).
Include what types of items (screenshots, datasets, diagrams) would be added.
"""
    }

    output = {}

    for section_title, prompt in sections_prompt.items():
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        output[section_title] = response.text.strip()

    return output


