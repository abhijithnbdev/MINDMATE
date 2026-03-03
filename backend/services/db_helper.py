from services.db import get_db, get_cursor
from sentence_transformers import SentenceTransformer
from datetime import datetime
from services.db import get_db

# services/db_helper.py
import psycopg2
from services.db import get_db, get_cursor


model = SentenceTransformer('all-MiniLM-L6-v2')
def get_smart_context(user_query, user_id):
    query_vec = model.encode(user_query).tolist()
    
    conn = get_db()
    cur = get_cursor(conn)
    
    try:
        # PostgreSQL syntax: Use %s instead of ?
        cur.execute("""
            SELECT original_text 
            FROM notes 
            WHERE user_id = %s 
            ORDER BY embedding <=> %s::vector 
            LIMIT 3;
        """, (user_id, query_vec))
        
        rows = cur.fetchall()
        # With RealDictCursor, row is a dictionary
        return "\n".join([row['original_text'] for row in rows])
    finally:
        cur.close()
        conn.close()

def log_chat(user_id, sender, text, location=None):
    conn = get_db()
    cur = conn.cursor() # Standard cursor is fine for simple inserts
    try:
        vec = model.encode(text).tolist()
        # Use %s for all 5 placeholders
        cur.execute(
            "INSERT INTO chat_messages (user_id, sender, text, location, embedding) VALUES (%s, %s, %s, %s, %s)",
            (user_id, sender, text, location, vec)
        )
        conn.commit()
    except Exception as e:
        print(f"Log Chat Error: {e}")
    finally:
        conn.close()
    conn = get_db()
    cur = conn.cursor()
    try:
        # Generate embedding for the chat text
        vec = model.encode(text).tolist()
        cur.execute(
            "INSERT INTO chat_messages (user_id, sender, text, location, embedding) VALUES (%s, %s, %s, %s, %s)",
            (user_id, sender, text, location, vec)
        )
        conn.commit()
    except Exception as e:
        print(f"Log Chat Error: {e}")
    finally:
        conn.close()
        
def get_semantic_context(user_query, user_id):
    # 1. Turn the user's question into a vector
    query_vec = model.encode(user_query).tolist()
    
    conn = get_db()
    cur = conn.cursor()
    
    # 2. Use the <=> operator (Cosine Distance) to find the top 3 closest notes
    cur.execute("""
        SELECT original_text 
        FROM notes 
        WHERE user_id = %s 
        ORDER BY embedding <=> %s::vector 
        LIMIT 3;
    """, (user_id, query_vec))
    
    context_chunks = cur.fetchall()
    return " ".join([c[0] for c in context_chunks])


def save_to_appropriate_table(user_id, analysis, origin_location="Gmail"):
    """
    Unified router to save data into specific tables based on AI analysis.
    """
    conn = get_db()
    cur = conn.cursor()
    
    # Extract the main data block and the classification
    data = analysis.get("data", {})
    category = analysis.get("type", "note").lower()
    
    try:
        # 1. SCHEDULES / EVENTS
        if category in ["event", "schedule"]:
            query = """
                INSERT INTO events (user_id, title, start_time, location_name, description, origin_location)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            start_time = data.get("date") or data.get("start_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(query, (
                user_id, 
                data.get("title", "New Event"), 
                start_time, 
                data.get("location"), 
                data.get("content") or data.get("description"),
                origin_location
            ))

        # 2. NOTES / MEMORIES (Vectorized)
        elif category == "note":
            content = data.get("content") or data.get("summary") or ""
            # Generate embedding for vector search
            vec = model.encode(content).tolist()
            query = """
                INSERT INTO notes (user_id, title, summary, original_text, origin_location, embedding) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cur.execute(query, (
                user_id, 
                data.get("title", "Email Note"), 
                data.get("title"), 
                content, 
                origin_location, 
                vec
            ))

        conn.commit()
        print(f"✅ Saved {category} to DB for {user_id}")
    except Exception as e:
        print(f"❌ DB Route Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()