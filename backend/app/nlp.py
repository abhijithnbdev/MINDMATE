# app/nlp.py
import os, json, re, requests, joblib, pandas as pd
from datetime import datetime, timedelta

from app.advanced_nlp import IntentAnalyzer
from rag.retriever import retrieve_context
from services.db_helper import save_to_appropriate_table
from services.db import get_db
from models.predictor import HabitEngine
from services.user_model_manager import get_habit_engine
from rag.prompt_builder import build_prompt
from services.events import get_schedule_for_date
from services.gmail import deep_sync_gmail


# ---------------- CONFIG ----------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/habit_model.pkl")

intent_analyzer = IntentAnalyzer()


from models.predictor import HabitEngine



# ---------------- UTIL ----------------
def humanize_datetime(dt: datetime) -> str:
    today = datetime.now().date()
    d = dt.date()

    if d == today:
        return f"today at {dt.strftime('%I:%M %p')}"
    if d == today - timedelta(days=1):
        return f"yesterday at {dt.strftime('%I:%M %p')}"
    if d == today + timedelta(days=1):
        return f"tomorrow at {dt.strftime('%I:%M %p')}"

    return dt.strftime('%Y-%m-%d at %I:%M %p')


def extract_date(text: str) -> str:
    t = text.lower()
    today = datetime.now().date()

    if "tomorrow" in t:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if "today" in t:
        return today.strftime("%Y-%m-%d")

    match = re.search(r"\d{4}-\d{2}-\d{2}", t)
    if match:
        return match.group(0)

    return today.strftime("%Y-%m-%d")

# ---------------- LLM ----------------
def call_llm(prompt: str) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
        timeout=60
    )
    return r.json().get("response", "").strip()

# ---------------- HABIT MODEL ----------------


def resolve_meal(hour: int, wake_hour: int = 7):
    if wake_hour <= hour <= wake_hour + 2:
        return "Breakfast"
    if 12 <= hour <= 14:
        return "Lunch"
    if 18 <= hour <= 20:
        return "Dinner"
    if (10 <= hour < 12) or (15 <= hour < 18):
        return "Snack"
    return None


# ---------------- PLANNING ----------------
def generate_blended_day_plan(user_id: str, date_str: str):
    # ✅ Initialize the engine here, inside the function
    habit_engine = get_habit_engine(user_id) 
    
    date = datetime.strptime(date_str, "%Y-%m-%d")
    day, month = date.weekday(), date.month

    timeline = {h: None for h in range(7, 23)}
    events = get_events_for_date(user_id, date_str)
    
    # ... rest of your code ...
    for h in range(7, 23):
        if timeline[h] is None:
            # ✅ Use the habit_engine created above
            act = habit_engine.predict(h, day, month) 
            # ...

# ---------------- MAIN ----------------
def generate_conversational_response(user_id: str, text: str):
    # --- STEP 1: PROACTIVE INTENT ANALYSIS ---
    routing_prompt = f"""
    Analyze the user input: "{text}"
    Categories:
    - 'email_sync': Checking/reading emails or asking "what's new in my mail?".
    - 'email_send': Explicit request to send, mail, or message someone.
    - 'general': Chatting, asking questions, or planning.
    
    Return ONLY the category name.
    """
    intent = call_llm(routing_prompt).lower().strip()

    # --- STEP 2: ROUTING ---
    
    # A. Proactive Sync + Summary
    if "email_sync" in intent:
        from services.gmail import deep_sync_gmail
        # 1. Perform the actual sync (saves to DB)
        deep_sync_gmail(user_id, count=3)
        
        # 2. Get the latest context from the DB to answer the user
        context = retrieve_context(user_id, "latest gmail updates")
        summary_prompt = f"""
            The user asked: {text}. 
            Data found in DB: {context}
            If the data is empty or irrelevant, say 'I couldn't find any recent emails.'
            Otherwise, provide a 2-sentence summary.
            """
        
        return call_llm(summary_prompt)

    # B. Send Email Logic
    if "email_send" in intent:
        # Assuming you have a handle_send_request function
        return handle_send_request(user_id, text)

    # C. Standard RAG Flow
    context = retrieve_context(user_id, text)
    final_prompt = build_prompt(text, context)
    
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": final_prompt, "stream": False},
            timeout=30
        )
        return r.json().get("response", "I'm having trouble thinking right now.")
    except Exception as e:
        return f"Connection error: {e}"
def analyze_conversation_payload(user_id: str, text: str) -> dict:
    """
    Extracts structured memory (note / schedule) from user input.
    Returns JSON only. No assumptions.
    """

    prompt = f"""
You are an information extractor.

Text:
"{text}"

Rules:
- If there is NO important information → return {{ "has_data": false }}
- Important info = schedules, meetings, reminders, notes, tasks
- Do NOT invent dates or times
- Return VALID JSON ONLY

Schema:
{{
  "has_data": true | false,
  "category": "note" | "schedule",
  "note": {{
    "title": "",
    "summary": "",
    "category": ""
  }},
  "schedule": {{
    "title": "",
    "start_time": "",
    "end_time": ""
  }}
}}
"""

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=30
        )
        return json.loads(r.json().get("response", "{}"))
    except Exception as e:
        return {"has_data": False}

def handle_send_request(user_id, text):
    from services.gmail import send_gmail_message
    
    # Simple extraction (You can make this better with another LLM call)
    # For now, let's use a hardcoded test to verify the connection
    recipient = "forgotitsorry1@gmail.com"
    subject = "Update from MindMate AI"
    body = f"Hello! This is an automated message from your MindMate Assistant regarding: {text}"
    
    result = send_gmail_message(user_id, recipient, subject, body)
    return result