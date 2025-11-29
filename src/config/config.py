
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]


class Config:

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    PINECONE_INDEX = "college-info-index"

    LLM_MODEL = "openai/gpt-oss-20b"

    CHUNK_SIZE = 400
    CHUNK_OVERLAP = 60

    DOCUMENT_SOURCES = [
        str(BASE_DIR / "data" / "saveetha.pdf"),
        str(BASE_DIR / "data" / "saveetha (2).pdf"),
        str(BASE_DIR / "data" / "faculty.pdf")
    ]

    @classmethod
    def get_llm(cls):
        return ChatGroq(
            model=cls.LLM_MODEL,
            temperature=0
        )