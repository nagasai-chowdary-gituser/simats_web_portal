
from typing import List, Optional
from pydantic import BaseModel, Field


class MemoryState(BaseModel):
    """Structured profile data we can reliably store per user."""

    user_name: Optional[str] = None
    preferred_name: Optional[str] = None
    roll_number: Optional[str] = None
    department: Optional[str] = None        # e.g., CSE, ECE
    year: Optional[str] = None              # e.g., 1st year, 3rd year
    hometown: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    custom_notes: List[str] = Field(default_factory=list)
    last_topic: Optional[str] = None

    def as_prompt_block(self) -> str:
        """Return a readable block for LLM prompts."""
        interests = ", ".join(self.interests) if self.interests else "-"
        notes = "; ".join(self.custom_notes) if self.custom_notes else "-"

        return (
            f"Name: {self.preferred_name or self.user_name or '-'}\n"
            f"Roll: {self.roll_number or '-'}\n"
            f"Department: {self.department or '-'}\n"
            f"Year: {self.year or '-'}\n"
            f"Hometown: {self.hometown or '-'}\n"
            f"Interests: {interests}\n"
            f"Notes: {notes}"
        )
