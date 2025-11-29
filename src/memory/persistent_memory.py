"""Lightweight JSON persistence for long-term, per-user memory."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

MEMORY_FILE = "memory/user_memory.json"


def _blank_store() -> Dict[str, Any]:
    return {"users": {}}


class PersistentMemory:

    @staticmethod
    def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return _blank_store()

        if "users" not in data or not isinstance(data["users"], dict):
            legacy_profile = data if data else {}
            users = {}
            if legacy_profile:
                users["__legacy__"] = {
                    "profile": legacy_profile,
                    "chat_history": []
                }
            return {"users": users}

        return data

    @staticmethod
    def load() -> Dict[str, Any]:
        os.makedirs("memory", exist_ok=True)

        if not os.path.exists(MEMORY_FILE):
            return _blank_store()

        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                raw = f.read().strip()
                if not raw:
                    return _blank_store()
                return PersistentMemory._normalize(json.loads(raw))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"⚠️ PersistentMemory load error: {exc}. Resetting memory store.")
            return _blank_store()

    @staticmethod
    def save(data: Dict[str, Any]):
        os.makedirs("memory", exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


class UserMemoryManager:
    """Helper to read/write individual user memories with capped history."""

    HISTORY_LIMIT = 30

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def _ensure_user(cls, store: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        users = store.setdefault("users", {})
        return users.setdefault(user_id, {
            "profile": {},
            "chat_history": []
        })

    @classmethod
    def fetch_context(cls, user_id: Optional[str]) -> Dict[str, Any]:
        if not user_id:
            user_id = "anonymous"

        store = PersistentMemory.load()
        user = store.get("users", {}).get(user_id, {
            "profile": {},
            "chat_history": []
        })

        return {
            "profile": user.get("profile", {}).copy(),
            "chat_history": list(user.get("chat_history", []))
        }

    @classmethod
    def persist(
        cls,
        user_id: Optional[str],
        *,
        profile: Optional[Dict[str, Any]] = None,
        turns: Optional[List[Dict[str, str]]] = None,
        last_topic: Optional[str] = None
    ):
        if not user_id:
            user_id = "anonymous"

        store = PersistentMemory.load()
        user = cls._ensure_user(store, user_id)

        if profile:
            sanitized = {
                key: value for key, value in profile.items()
                if value not in (None, "", [])
            }
            if sanitized:
                user.setdefault("profile", {}).update(sanitized)

        if last_topic:
            user.setdefault("profile", {})["last_topic"] = last_topic

        if turns:
            valid_turns = []
            for turn in turns:
                content = (turn.get("content") or "").strip()
                role = turn.get("role") or "assistant"
                if not content:
                    continue
                valid_turns.append({
                    "role": role,
                    "content": content[:2000]
                })

            if valid_turns:
                history = user.setdefault("chat_history", [])
                history.extend(valid_turns)
                user["chat_history"] = history[-cls.HISTORY_LIMIT:]

        user["updated_at"] = cls._utc_timestamp()
        PersistentMemory.save(store)
