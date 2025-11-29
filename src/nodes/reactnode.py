"""Agentic ReAct RAG node with individualized memory + Markdown output."""

import re
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from src.state.rag_state import RAGState
from src.state.memory_state import MemoryState
from src.memory.persistent_memory import UserMemoryManager


class RAGNodes:
    URL_PATTERN = re.compile(r"https?://[^\s)]+", re.IGNORECASE)

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self.agent = None

    @staticmethod
    def _update_state(state, **updates):
        if hasattr(state, "model_copy"):
            return state.model_copy(update=updates)
        merged = dict(state)
        merged.update(updates)
        return merged

    # -----------------------------------------------------------
    # TOOL: RAG RETRIEVAL
    # -----------------------------------------------------------
    def build_tools(self):

        @tool
        def campus_search(query: str):
            """Search indexed college documents (courses, fees, faculty, rules, etc.) and return the most relevant text."""
            docs = self.retriever.invoke(query)
            if not docs:
                return "NO_DOC_DATA"
            return "\n\n".join([d.page_content.strip() for d in docs[:6]])

        return [campus_search]

    def build_agent(self):
        self.agent = create_react_agent(self.llm, tools=self.build_tools())

    # -----------------------------------------------------------
    # MEMORY + HISTORY HELPERS
    # -----------------------------------------------------------
    def _prepare_memory(self, state: RAGState) -> MemoryState:
        memory = state.memory
        if isinstance(memory, dict):
            memory = MemoryState(**memory)
        return memory

    def _extract_memory(self, text: str, memory: MemoryState) -> MemoryState:
        lowered = text.lower()

        name_match = re.search(r"(?:my name is|call me|i am)\s+([a-z][a-z\s]{1,40})", lowered, re.IGNORECASE)
        if name_match:
            memory.preferred_name = name_match.group(1).strip().title()
            memory.user_name = memory.user_name or memory.preferred_name

        roll_match = re.search(r"(?:roll(?: number)?|register(?: number)?)\s*(?:no\.?|number)?\s*(?:is)?\s*([a-z0-9-/]+)", lowered, re.IGNORECASE)
        if roll_match:
            memory.roll_number = roll_match.group(1).replace(" ", "").upper()

        if "remember that" in lowered:
            note = text.split("remember that", 1)[1].strip()
            if note and note not in memory.custom_notes:
                memory.custom_notes.append(note)
                if len(memory.custom_notes) > 5:
                    memory.custom_notes.pop(0)

        return memory

    def _chat_history_block(self, history):
        if not history:
            return "No earlier conversation."
        recent = history[-6:]
        lines = []
        for turn in recent:
            role = (turn.get("role") or "user").capitalize()
            content = turn.get("content") or ""
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

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

    # -----------------------------------------------------------
    # AGENTIC ANSWER
    # -----------------------------------------------------------
    def generate_answer(self, state: RAGState) -> RAGState:

        if not self.agent:
            self.build_agent()

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
            updated_history = (state.chat_history + [
                {"role": "user", "content": state.question},
                {"role": "assistant", "content": answer}
            ])[-UserMemoryManager.HISTORY_LIMIT:]
            return self._update_state(state, answer=answer, memory=memory, chat_history=updated_history)

        if "remember" in state.question.lower() and "about me" in state.question.lower():
            summary = memory.as_prompt_block()
            answer = "🧠 Here's what I currently remember about you:\n\n" + summary
            UserMemoryManager.persist(
                state.user_id,
                profile=memory.model_dump(),
                turns=[
                    {"role": "user", "content": state.question},
                    {"role": "assistant", "content": answer}
                ]
            )
            updated_history = (state.chat_history + [
                {"role": "user", "content": state.question},
                {"role": "assistant", "content": answer}
            ])[-UserMemoryManager.HISTORY_LIMIT:]
            return self._update_state(state, answer=answer, memory=memory, chat_history=updated_history)

        history_block = self._chat_history_block(state.chat_history)
        greet = f"🎓 Hi {memory.preferred_name or memory.user_name}!" if (memory.preferred_name or memory.user_name) else "🎓 Hi there!"

        system = SystemMessage(
            content=f"""
You are **CampusBuddy Pro**, an advanced agentic assistant.

==========================
✨ STYLE
==========================
- Clear section headers (Overview, Fees, Deadlines...)
- Use Markdown lists for clarity.
- Provide Markdown tables only when the user specifically requests a table or asks for a comparison grid.
- Format every raw URL as a Markdown link so it becomes clickable in the UI.
- Only reveal phone numbers/emails when the user clearly requests contact details (phone, contact, faculty number, etc.).
- Whenever you share phone/email, keep the faculty/staff name with it on the same bullet (e.g., "• Dr. Priya Sharma — Phone: 98765 43210").
- If the user asks for a faculty phone number or who a number belongs to, include both the name and the number if possible.
- Base every answer strictly on the 📘 DOCUMENT CONTEXT and stored memory; if the PDFs do not mention the requested fact, say "I'm not sure" and suggest contacting the college office instead of guessing.
- Friendly emojis (🎓✨📘) encouraged; no chain-of-thought.

==========================
🧠 USER PROFILE
==========================
{memory.as_prompt_block()}

==========================
💬 RECENT CHAT
==========================
{history_block}

==========================
🔐 SENSITIVE DATA
==========================
Only share phone/email when the user explicitly asks; otherwise redact with [contact hidden].

Begin replies with: {greet}
"""
        )

        result = self.agent.invoke({
            "messages": [system, HumanMessage(content=state.question)]
        })

        raw_answer = result["messages"][-1].content
        cleaned = re.sub(r"\n{3,}", "\n\n", raw_answer.strip())
        cleaned = self._linkify(cleaned)
        cleaned = self._filter_sensitive(state.question, cleaned)

        turns = [
            {"role": "user", "content": state.question},
            {"role": "assistant", "content": cleaned}
        ]

        UserMemoryManager.persist(
            state.user_id,
            profile=memory.model_dump(),
            turns=turns,
            last_topic=state.question
        )

        updated_history = (state.chat_history + turns)[-UserMemoryManager.HISTORY_LIMIT:]

        return self._update_state(state, answer=cleaned, memory=memory, chat_history=updated_history)
