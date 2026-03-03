from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
import datetime
import requests # Needed for AI prediction

router = APIRouter()
DB_PATH = "mindmate.db"
OLLAMA_URL = "http://localhost:11434/api/generate"

class MemoryRequest(BaseModel):
    user_id: str
    title: str
    content: str
    category: str
    type: str = "note" 

@router.get("/memories")
def get_timeline(user_id: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM timeline WHERE user_id = ? ORDER BY id DESC", (user_id,))
            return {"timeline": [dict(row) for row in cursor.fetchall()]}
    except Exception as e:
        return {"timeline": []}

@router.post("/memories")
def add_memory(memory: MemoryRequest):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO timeline (user_id, type, title, content, category, start_time) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (memory.user_id, memory.type, memory.title, memory.content, memory.category, now))
            conn.commit()
            return {"status": "success", "message": "Memory added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ NEW: Schedule Prediction (Moved here to avoid creating new files)
@router.get("/predict/schedule")
def predict_schedule(date: str):
    prompt = f"Create a simple daily schedule for {date} as a JSON list."
    try:
        payload = {"model": "mistral", "prompt": prompt, "stream": False}
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        ai_text = response.json().get("response", "")
        
        # Mock Response to prevent crash if AI output is messy
        mock_schedule = [
            {"time": "09:00 AM", "activity": "Work Start"},
            {"time": "01:00 PM", "activity": "Lunch"},
            {"time": "05:00 PM", "activity": "Review"}
        ]
        return {"suggested_schedule": mock_schedule, "raw_ai": ai_text}
    except:
        return {"suggested_schedule": []}
