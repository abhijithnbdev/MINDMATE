# app/nlp.py
import os, json, re, requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"

def call_llm(prompt: str, format_json: bool = False) -> str:
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    if format_json: payload["format"] = "json"
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        return r.json().get("response", "").strip()
    except Exception as e:
        return "{}" if format_json else "Error"

def classify_audio_intent(transcript: str) -> dict:
    """Analyzes intent, emotion, and determines if security-sensitive CRUD is needed."""
    prompt = f"""
    Analyze this transcript: "{transcript}"
    
    1. DECISION: 
       - 'CRUD' if user wants to READ, DELETE, or SEARCH past data/history.
       - 'TASK' if user wants to ADD a new reminder.
       - 'ARCHIVE' if it's info to save (lecture/meeting).
       - 'IGNORE' if noise.
    2. EMOTION: Urgent, Stressed, Neutral, or Happy.
    3. ACTION: 'READ', 'DELETE', 'UPDATE', or 'CREATE'.

    Return ONLY JSON with these fields:
        - "decision": "CRUD", "TASK", "ARCHIVE", or "IGNORE"
        - "category": "meeting", "reminder", "history", "note", "schedule", or "medicine"
        - "emotion": "Urgent" or "Neutral"
        - "action": "READ", "DELETE", "UPDATE", "CREATE", or "NONE"
        - "priority": "High" or "Low"
        - "search_query": "A 1-sentence summary of what was said for the database summary column"
        """
    response_str = call_llm(prompt, format_json=True)
    try:
        data = json.loads(response_str)
        if data.get("emotion") == "Urgent" or data.get("category") == "meeting" or data.get("category") == "schedule":
            data["priority"] = "High"
        return data
    except:
        return {"decision": "IGNORE", "category": "note", "emotion": "Neutral"}

def generate_conversational_response(user_id: str, text: str) -> str:
    """Uses RAG to answer as a Personal Assistant."""
    from rag.retriever import retrieve_combined_context
    
    context = retrieve_combined_context(user_id, text)
    
    assistant_prompt = f"""
    You are 'MindMate', a helpful personal AI assistant. 
    User Query: "{text}"
    
    User's Data Context:
    {context}
    
    Instructions:
    - Use the context to answer specifically about the user's past, doubts, or plans.
    - If the user asks a question, act as a knowledgeable assistant.
    - If data is missing from context, answer generally but mention you don't see it in their records.
    - Be friendly, brief, and professional.
    """
    return call_llm(assistant_prompt)

def analyze_conversation_payload(user_id: str, text: str) -> dict:
    prompt = f"Extract info from: '{text}'. Return JSON with 'has_data', 'category', 'note', 'schedule'."
    try:
        return json.loads(call_llm(prompt, format_json=True))
    except:
        return {"has_data": False}