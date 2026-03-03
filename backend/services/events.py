import psycopg2
from psycopg2.extras import RealDictCursor
from services.db import get_db

def save_voice_entry(user_id, original_text, analysis):
    conn = get_db()
    cur = conn.cursor()
    try:
        category = analysis.get("category", "none")
        saved_message = None

        if category == "schedule" and analysis.get("schedule"):
            evt = analysis["schedule"]
            cur.execute("""
                INSERT INTO events (user_id, title, category, start_time, end_time, location_name) 
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """, (user_id, evt.get("title"), "personal", evt.get("start_time"), evt.get("end_time"), evt.get("location")))
            
            event_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO voice_analysis (user_id, associated_event_id, original_transcript, stress_level) 
                VALUES (%s, %s, %s, %s)
            """, (user_id, event_id, original_text, 0.0))
            saved_message = f"✅ Scheduled: {evt.get('title')}"

        elif category == "note" and analysis.get("note"):
            note = analysis["note"]
            cur.execute("""
                INSERT INTO memories (user_id, memory_type, title, content)
                VALUES (%s, %s, %s, %s)
            """, (user_id, "general_note", note.get("title"), note.get("content", original_text)))
            saved_message = f"✅ Saved Note: {note.get('title')}"

        conn.commit()
        return saved_message
    except Exception as e:
        conn.rollback()
        print(f"❌ DB Error: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_schedule_for_date(user_id: str, date_str: str):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT title, start_time, location_name FROM events 
            WHERE user_id = %s AND date(start_time) = %s ORDER BY start_time ASC
        """, (user_id, date_str))
        rows = cur.fetchall()
        
        events = []
        for row in rows:
            time = str(row['start_time']).split(' ')[1][:5] if ' ' in str(row['start_time']) else "00:00"
            loc = f" at {row['location_name']}" if row['location_name'] else ""
            events.append(f"- {time}: {row['title']}{loc}")
        return events
    finally:
        cur.close()
        conn.close()