from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
import psycopg2.extras
from psycopg2.extras import RealDictCursor
from services.db import get_db, get_cursor

router = APIRouter(tags=["Reminders"])

# --- MODELS ---

class ToggleRequest(BaseModel):
    reminder_id: int
    is_active: bool

class ReminderCreate(BaseModel):
    user_id: str
    message: str
    trigger_time: datetime  # Accepts ISO 8601 string from Flutter
    priority_level: str

# --- ROUTES ---

@router.get("/")
async def get_reminders(user_id: str = Query(...)):
    """
    Fetches all reminders for a specific user.
    Aliases columns to match Flutter expectations (title, remind_time).
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT 
                id, 
                message as title, 
                TO_CHAR(trigger_time, 'HH12:MI AM') as remind_time, 
                trigger_time as raw_time,
                status,
                priority_level,
                priority
            FROM reminders 
            WHERE user_id = %s 
            ORDER BY priority ASC, trigger_time ASC
        """, (user_id,))
        
        rows = cur.fetchall()
        
        # Convert 'active' string status to boolean for Flutter Switch widgets
        for row in rows:
            row['is_active'] = (row['status'] == 'active')
            # Convert datetime objects to strings if not already handled
            if isinstance(row['raw_time'], datetime):
                row['raw_time'] = row['raw_time'].isoformat()
            
        return {"reminders": rows}
    except Exception as e:
        print(f"Database Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reminders")
    finally:
        cur.close()
        conn.close()

@router.post("/toggle")
async def toggle_reminder(data: ToggleRequest):
    """
    Updates the status of a reminder (active vs inactive).
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        new_status = 'active' if data.is_active else 'inactive'
        cur.execute(
            "UPDATE reminders SET status = %s WHERE id = %s",
            (new_status, data.reminder_id)
        )
        conn.commit()
        return {"status": "success", "new_status": new_status}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@router.post("/create")
async def create_new_reminder(data: ReminderCreate):
    """
    Inserts a new reminder with a specific timestamp.
    Defaults priority to 2 (Medium) if not specified.
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        # Map priority_level text to numerical priority
        priority_map = {"High": 1, "Medium": 2, "Low": 3}
        num_priority = priority_map.get(data.priority_level, 3)

        cur.execute("""
            INSERT INTO reminders (user_id, message, trigger_time, status, priority_level, priority)
            VALUES (%s, %s, %s, 'active', %s, %s)
            RETURNING id
        """, (data.user_id, data.message, data.trigger_time, data.priority_level, num_priority))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        
        return {
            "status": "success", 
            "message": "Reminder created", 
            "reminder_id": new_id
        }
    except Exception as e:
        conn.rollback()
        print(f"Insert Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create reminder")
    finally:
        cur.close()
        conn.close()
 

@router.get("/filter")
async def get_filtered_reminders(user_id: str, priorities: List[str] = Query(None)):
    conn = get_db()
    # RealDictCursor ensures we get a dictionary for Flutter to parse easily
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        query = "SELECT * FROM reminders WHERE user_id = %s"
        params = [user_id]
        
        if priorities:
            query += " AND priority_level = ANY(%s)"
            params.append(priorities)
            
        query += " ORDER BY trigger_time ASC"
        cur.execute(query, params)
        return {"reminders": cur.fetchall()}
    finally:
        cur.close()
        conn.close()
               
@router.delete("/delete/{reminder_id}")
async def delete_reminder(reminder_id: int):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM reminders WHERE id = %s", (reminder_id,))
        conn.commit()
        return {"status": "success", "message": "Reminder deleted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()# app/routers/reminders.py changes


@router.get("/organized")
async def get_organized_tasks(user_id: str = Query(...)):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # High Priority -> Reminders Page
        cur.execute("""
            SELECT id, message as title, TO_CHAR(trigger_time, 'HH12:MI AM') as remind_time, 
            status, priority_level FROM reminders 
            WHERE user_id = %s AND priority = 1 AND status = 'active'
            ORDER BY trigger_time ASC
        """, (user_id,))
        reminders = cur.fetchall()

        # Med/Low Priority -> Todo Page
        cur.execute("""
            SELECT id, message as title, trigger_time, priority_level FROM reminders 
            WHERE user_id = %s AND priority > 1 AND status = 'active'
            ORDER BY priority ASC, trigger_time ASC
        """, (user_id,))
        todos = cur.fetchall()

        return {"reminders": reminders, "todos": todos}
    finally:
        cur.close()
        conn.close()

# Keep your existing /, /toggle, /create, and /delete routes...