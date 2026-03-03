# app/advanced_nlp.py
import re

class IntentAnalyzer:
    def analyze(self, text: str):
        t = text.lower().strip()

        # 1️⃣ Retrieval (past / memory)
        if any(k in t for k in [
            "what was", "what is my", "previous",
            "history", "when was", "where was",
            "show me", "strategy", "appointment"
        ]):
            return {"type": "retrieval"}

        # 2️⃣ Future planning
        if any(k in t for k in [
            "plan for", "schedule for",
            "timetable for", "routine for",
            "tomorrow", "next day", "next week"
        ]):
            return {"type": "future_plan"}

        # 3️⃣ Store commands
        if any(k in t for k in [
            "save", "note", "remember",
            "add", "schedule", "set a reminder"
        ]):
            return {"type": "store"}

        return {"type": "chat"}
