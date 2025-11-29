
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.documents import Document
from src.state.memory_state import MemoryState


class RAGState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    question: str
    user_id: Optional[str] = None
    memory: MemoryState = Field(default_factory=MemoryState)
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    retrieved_docs: List[Document] = Field(default_factory=list)
    answer: Optional[str] = ""
