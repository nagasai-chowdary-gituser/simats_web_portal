"""Simple (non-agentic) RAG nodes with per-user memory + clean Markdown output."""

import re
from typing import List
from langchain_core.documents import Document
from src.state.rag_state import RAGState
from src.state.memory_state import MemoryState
from src.memory.persistent_memory import UserMemoryManager


class RAGNodes:
    DEPARTMENTS = [
        "cse", "ece", "eee", "it", "civil",
        "mechanical", "mech", "ai&ds", "aiml", "bme"
    ]
    URL_PATTERN = re.compile(r"https?://[^\s)]+", re.IGNORECASE)

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm

    @staticmethod
    def _update_state(state, **updates):
        if hasattr(state, "model_copy"):
            return state.model_copy(update=updates)
        merged = dict(state)
        merged.update(updates)
        return merged

    # -------------------------------------------------------------
    # NODE 1 — RETRIEVAL
    # -------------------------------------------------------------
    def retrieve_docs(self, state: RAGState) -> RAGState:
        docs: List[Document] = self.retriever.invoke(state.question)
        return self._update_state(state, retrieved_docs=docs)

    # -------------------------------------------------------------
    # MEMORY HELPERS
    # -------------------------------------------------------------
    def _prepare_memory(self, state: RAGState) -> MemoryState:
        memory = state.memory
        if isinstance(memory, dict):
            memory = MemoryState(**memory)
        return memory

    def _store_unique(self, bucket: List[str], value: str, limit: int = 5):
        cleaned = value.strip()
        if not cleaned:
            return
        if cleaned not in bucket:
            bucket.append(cleaned)
            if len(bucket) > limit:
                bucket.pop(0)

    def _extract_memory(self, text: str, memory: MemoryState) -> MemoryState:
        lowered = text.lower()

        name_match = re.search(r"(?:my name is|call me|i am)\s+([a-z][a-z\s]{1,40})", lowered, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip().title()
            memory.user_name = memory.user_name or name
            memory.preferred_name = name

        roll_match = re.search(r"(?:roll(?: number)?|register(?: number)?)\s*(?:no\.?|number)?\s*(?:is)?\s*([a-z0-9-/]+)", lowered, re.IGNORECASE)
        if roll_match:
            memory.roll_number = roll_match.group(1).replace(" ", "").upper()

        dept_match = re.search(r"(?:i am|i'm|i study|dept is)\s+(?:in\s+)?([a-z&]+)", lowered)
        if dept_match:
            dept_val = dept_match.group(1).replace("&", "").replace(" ", "").lower()
            for dept in self.DEPARTMENTS:
                if dept in dept_val:
                    memory.department = dept.upper()
                    break

        year_match = re.search(r"(?:i am|i'm|currently)\s+(?:in\s+)?(\d(?:st|nd|rd|th)?\s*year)", lowered)
        if year_match:
            memory.year = year_match.group(1).replace(" ", "")

        hometown_match = re.search(r"i am from\s+([a-z\s]+)", lowered)
        if hometown_match and not memory.hometown:
            memory.hometown = hometown_match.group(1).strip().title()

        interest_match = re.findall(r"(?:i like|my interest(?:s)? (?:are|is)|i love)\s+([^.,;]+)", text, re.IGNORECASE)
        for interest in interest_match:
            self._store_unique(memory.interests, interest.strip().title())

        if "remember that" in lowered:
            note = text.split("remember that", 1)[1].strip()
            if note:
                self._store_unique(memory.custom_notes, note)

        return memory

    def _chat_history_block(self, history: List[dict]) -> str:
        if not history:
            return "No earlier messages in this session."
        recent = history[-6:]
        lines = []
        for turn in recent:
            role = (turn.get("role") or "user").capitalize()
            content = turn.get("content") or ""
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    # -------------------------------------------------------------
    # OUTPUT CLEANUP
    # -------------------------------------------------------------
    def _filter_sensitive(self, question: str, answer: str) -> str:
        q = question.lower()
        contact_terms = ["phone", "mobile", "contact", "email", "call", "tel", "telephone"]
        explicit = any(x in q for x in contact_terms)

        if not explicit:
            faculty_terms = ["faculty", "facuty", "professor", "staff", "hod", "dean", "advisor", "lecturer"]
            number_terms = ["number", "no", "contact", "phone", "mobile", "email"]
            explicit = any(f in q for f in faculty_terms) and any(n in q for n in number_terms)

        if explicit:
            return answer

        answer = re.sub(r"\b\d{10,}\b", "[contact hidden]", answer)
        answer = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+", "[email hidden]", answer)
        return answer

    def _linkify(self, text: str) -> str:
        result = []
        last_idx = 0
        for match in self.URL_PATTERN.finditer(text):
            start, end = match.span()
            result.append(text[last_idx:start])
            already_linked = start >= 2 and text[start-2:start] == "]("
            url = match.group(0)
            if already_linked:
                result.append(url)
            else:
                result.append(f"[{url}]({url})")
            last_idx = end
        result.append(text[last_idx:])
        return "".join(result)

    # -------------------------------------------------------------
    # NODE 2 — ANSWER GENERATION
    # -------------------------------------------------------------
    def generate_answer(self, state: RAGState) -> RAGState:
        memory = self._prepare_memory(state)
        memory = self._extract_memory(state.question, memory)

        if "what is my name" in state.question.lower():
            name = memory.preferred_name or memory.user_name
            answer = f"Your name is {name}." if name else "You haven't told me your name yet."
            UserMemoryManager.persist(
                state.user_id,
                profile=memory.model_dump(),
                turns=[
                    {"role": "user", "content": state.question},
                    {"role": "assistant", "content": answer}
                ]
            )
            new_history = (state.chat_history + [
                {"role": "user", "content": state.question},
                {"role": "assistant", "content": answer}
            ])[-UserMemoryManager.HISTORY_LIMIT:]
            return self._update_state(state, answer=answer, memory=memory, chat_history=new_history)

        if "remember" in state.question.lower() and "about me" in state.question.lower():
            snapshot_lines = memory.as_prompt_block()
            answer = "🧠 Here's what I currently remember about you:\n\n" + snapshot_lines
            UserMemoryManager.persist(
                state.user_id,
                profile=memory.model_dump(),
                turns=[
                    {"role": "user", "content": state.question},
                    {"role": "assistant", "content": answer}
                ]
            )
            new_history = (state.chat_history + [
                {"role": "user", "content": state.question},
                {"role": "assistant", "content": answer}
            ])[-UserMemoryManager.HISTORY_LIMIT:]
            return self._update_state(state, answer=answer, memory=memory, chat_history=new_history)

        context = "\n\n".join(
            doc.page_content.strip() for doc in state.retrieved_docs[:6]
        ) if state.retrieved_docs else "No matching document chunks found."

        history_block = self._chat_history_block(state.chat_history)
        greet = f"🎓 Hi {memory.preferred_name or memory.user_name}!" if (memory.preferred_name or memory.user_name) else "🎓 Hi there!"

        prompt = f"""
You are **CampusBuddy**, a friendly AI assistant for our college.

==========================
✨ STYLE & OUTPUT
==========================
- Write in clean Markdown.
- Use bullet points for steps/fees.
- If user explicitly asks for a table, return a concise Markdown table.
- When sharing URLs from the documents, format them as Markdown links so they are clickable.
- Only provide phone numbers/emails when the user clearly requests them (keywords like phone, contact, faculty number, etc.).
- Whenever you share a phone/email, include the related faculty/staff name in the same line (e.g., "• Dr. Priya Sharma — Phone: 98765 43210").
- If someone asks for a faculty phone number (or whose number it is), give both the name and the number when available.
- Base every factual detail strictly on the 📘 DOCUMENT CONTEXT (and obvious user profile info). If the PDFs don't mention something, say "I'm not sure" and invite them to check with the college office.
- Keep the tone light with emojis like 🎓✨📘.
- Say "I'm not sure" when info is missing.

==========================
🧠 USER PROFILE
==========================
{memory.as_prompt_block()}

==========================
💬 RECENT CHAT
==========================
{history_block}

==========================
📘 DOCUMENT CONTEXT
==========================
{context}

==========================
USER QUESTION
==========================
{state.question}

Begin your response with: {greet}
"""

        output = self.llm.invoke(prompt)
        answer = getattr(output, "content", str(output)).strip()
        answer = re.sub(r"\n{3,}", "\n\n", answer)
        answer = self._linkify(answer)
        answer = self._filter_sensitive(state.question, answer)

        turns = [
            {"role": "user", "content": state.question},
            {"role": "assistant", "content": answer}
        ]

        UserMemoryManager.persist(
            state.user_id,
            profile=memory.model_dump(),
            turns=turns,
            last_topic=state.question
        )

        updated_history = (state.chat_history + turns)[-UserMemoryManager.HISTORY_LIMIT:]

        return self._update_state(state, answer=answer, memory=memory, chat_history=updated_history)
