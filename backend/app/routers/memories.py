from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import requests
from datetime import datetime
import datetime as dt 
from services.db import get_db
from psycopg2.extras import RealDictCursor
from models.predictor import HabitEngine # 🟢 Uses the updated Engine with LabelEncoder

# Single router definition
router = APIRouter(tags=["Memories & Planner"])

OLLAMA_URL = "http://localhost:11434/api/generate"

class MemoryRequest(BaseModel):
    user_id: str
    title: str
    content: str
    category: str
    type: str = "note"

# --- 1. TIMELINE & MEMORY MANAGEMENT ---

@router.get("/")
async def get_memories(user_id: str = Query(...)):
    """Fetches user memories/timeline for the Life Overview."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, type, title, content, category, start_time as created_at 
            FROM timeline 
            WHERE user_id = %s 
            ORDER BY id DESC
        """, (user_id,))
        rows = cur.fetchall()
        return {"timeline": rows if rows else []}
    finally:
        cur.close()
        conn.close()

@router.post("/memories")
def add_memory(memory: MemoryRequest):
    """Adds a manual entry to the timeline."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO timeline (user_id, type, title, content, category, start_time) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (memory.user_id, memory.type, memory.title, memory.content, memory.category, now))
        conn.commit()
        return {"status": "success", "message": "Memory added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# --- 2. AI FUTURE PLANNER (Predictive Logic) ---

@router.get("/predict-timetable")
async def predict_timetable(user_id: str, target_date: str):
    """
    Core AI logic. Uses the trained Random Forest model to 
    generate a 24-hour forecast based on user habits.
    """
    try:
        # 1. Parse date to extract DayOfWeek and Month
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        
        # 2. Initialize Engine (which loads the .pkl + LabelEncoder)
        engine = HabitEngine(user_id)
        
        timetable = []
        for h in range(24):
            # 🤖 AI Prediction
            # Predict uses: Hour (h), DayOfWeek (0-6), Month (1-12)
            activity = engine.predict(h, date_obj.weekday(), date_obj.month)
            
            timetable.append({
                "time": f"{h:02d}:00",
                "activity": activity
            })
            
        # Matches Flutter: aiSchedule = data['timetable']
        return {"timetable": timetable}
    except Exception as e:
        print(f"❌ Planner Error: {e}")
        return {"error": str(e), "timetable": []}

# --- 3. OLLAMA FALLBACK ---

@router.get("/predict/schedule")
def predict_schedule_ollama(date: str):
    """Optional LLM-based fallback for general planning."""
    mock_schedule = [
        {"time": "09:00 AM", "activity": "Work Start"},
        {"time": "01:00 PM", "activity": "Lunch"},
        {"time": "05:00 PM", "activity": "Review"}
    ]
    return {"suggested_schedule": mock_schedule}