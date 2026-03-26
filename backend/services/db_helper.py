import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dateutil.parser import parse as date_parse
from sentence_transformers import SentenceTransformer
from services.db import get_db, get_cursor
from datetime import datetime
from rag.embedder import embed_text

# Load the vector model (optimized for your Ryzen 7)
model = SentenceTransformer('all-MiniLM-L6-v2')
def save_to_appropriate_table(user_id, analysis, original_text=""):
    conn = get_db()
    cur = conn.cursor()
    
    category = analysis.get("category", "note").lower()
    decision = analysis.get("decision", "STORE").upper()
    priority = analysis.get("priority", "Low")
    emotion = analysis.get("emotion", "Neutral")
    # 🟢 NEW: Extract the summary/topic from the NLP analysis
    summary = analysis.get("search_query") or analysis.get("topic") or "No summary"

    try:
        if decision == "IGNORE":
            return "💤 Background noise ignored."

        # 1. OFFICIAL/URGENT -> Reminders
        if category in ["meeting", "deadline", "task", "schedule", "medicine"] or priority == "High" or emotion == "Urgent":
            num_priority = 1 if (priority == "High" or emotion == "Urgent") else 2
            cur.execute("""
                INSERT INTO reminders (user_id, message, status, priority, priority_level, trigger_time)
                VALUES (%s, %s, 'active', %s, %s, NOW() + INTERVAL '1 hour')
            """, (user_id, original_text, num_priority, priority))
            conn.commit()
            return f"🚨 Recorded {priority} Priority {category.upper()}"

        # 2. CONTINUOUS CAPTURE (Stitching Logic)
        if category in ["lecture", "meeting"] or decision == "ARCHIVE":
            cur.execute("""
                UPDATE notes SET 
                    original_text = original_text || ' ' || %s, 
                    summary = %s,
                    updated_at = NOW()
                WHERE user_id = %s AND category = %s AND updated_at > NOW() - INTERVAL '15 minutes'
                RETURNING id;
            """, (original_text, summary, user_id, category))
            
            if cur.fetchone():
                conn.commit()
                return f"📝 Appended to ongoing {category}"

            # 🟢 Create new session: Save both text and summary
            vec = embed_text(original_text)
            cur.execute("""
                INSERT INTO notes (user_id, title, original_text, summary, category, embedding) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, f"{category.capitalize()} Session", original_text, summary, category, vec))
            conn.commit()
            return f"🎓 Recorded background {category}"

        # 3. GENERAL MEMORIES
        else:
            vec = embed_text(original_text)
            cur.execute("""
                INSERT INTO notes (user_id, title, original_text, summary, category, embedding) 
                VALUES (%s, %s, %s, %s, 'background', %s)
            """, (user_id, f"Voice Memo ({emotion})", original_text, summary, vec))
            conn.commit()
            return "✅ Background context saved."

    except Exception as e:
        conn.rollback()
        return f"Error: {str(e)}"
    finally:
        cur.close()
        conn.close()
        
        
def format_fuzzy_timestamp(time_str):
    """
    Translates fuzzy AI extractions (like 'evening') into DB-valid timestamps.
    Prevents: invalid input syntax for type timestamp.
    """
    if not time_str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    t = str(time_str).lower().strip()
    now = datetime.now()
    
    # Logic for common LLM fuzzy extractions
    target_date = now
    if "tomorrow" in t:
        target_date = now + timedelta(days=1)
    elif "next week" in t:
        target_date = now + timedelta(days=7)

    # Time offsets
    if "morning" in t:
        hour, minute = 9, 0
    elif "afternoon" in t:
        hour, minute = 14, 0
    elif "evening" in t:
        hour, minute = 18, 0
    elif "night" in t:
        hour, minute = 21, 0
    else:
        # Try a hard parse if it's not a fuzzy keyword
        try:
            return date_parse(t).strftime("%Y-%m-%d %H:%M:%S")
        except:
            # Fallback to current time + 1 hour if totally unparseable
            return (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

    return target_date.replace(hour=hour, minute=minute, second=0).strftime("%Y-%m-%d %H:%M:%S")

def get_semantic_context(user_query, user_id):
    """Finds the top 3 most relevant notes using vector similarity."""
    query_vec = model.encode(user_query).tolist()
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT original_text 
            FROM notes 
            WHERE user_id = %s 
            ORDER BY embedding <=> %s::vector 
            LIMIT 3;
        """, (user_id, query_vec))
        
        context_chunks = cur.fetchall()
        return " ".join([c[0] for c in context_chunks if c[0]])
    finally:
        cur.close()
        conn.close()

def log_chat(user_id, sender, text, location=None):
    """Logs chat interactions with vector embeddings for RAG retrieval."""
    conn = get_db()
    cur = conn.cursor()
    try:
        vec = model.encode(text).tolist()
        cur.execute("""
            INSERT INTO chat_messages (user_id, sender, text, location, embedding) 
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, sender, text, location, vec))
        conn.commit()
    except Exception as e:
        print(f"❌ Log Chat Error: {e}")
    finally:
        cur.close()
        conn.close()





def save_to_appropriate_table(user_id, analysis, original_text=""):
    """
    Saves context silently to the DB. 
    This is 'Passive Monitoring'. Everything is stored for RAG, 
    but retrieval is blocked in the router if the voice isn't verified.
    """
    conn = get_db()
    cur = conn.cursor()
    
    category = analysis.get("category", "note").lower()
    decision = analysis.get("decision", "STORE").upper()
    priority = analysis.get("priority", "Low")
    emotion = analysis.get("emotion", "Neutral")

    try:
        if decision == "IGNORE":
            return "💤 Background noise ignored."

        # 1. OFFICIAL/URGENT -> Reminders (Stays in DB for the owner)
        if category in ["meeting", "deadline", "task", "schedule"] or priority == "High" or emotion == "Urgent":
            num_priority = 1 if (priority == "High" or emotion == "Urgent") else 2
            cur.execute("""
                INSERT INTO reminders (user_id, message, status, priority, priority_level, trigger_time)
                VALUES (%s, %s, 'active', %s, %s, NOW() + INTERVAL '1 hour')
            """, (user_id, original_text, num_priority, priority))
            conn.commit()
            return f"🚨 Recorded {priority} Priority {category.upper()}"

        # 2. CONTINUOUS CAPTURE (Stitching Logic)
        if category in ["lecture", "meeting"] or decision == "ARCHIVE":
            cur.execute("""
                UPDATE notes SET original_text = original_text || ' ' || %s, updated_at = NOW()
                WHERE user_id = %s AND category = %s AND updated_at > NOW() - INTERVAL '15 minutes'
                RETURNING title;
            """, (original_text, user_id, category))
            
            if cur.fetchone():
                conn.commit()
                return f"📝 Appended to ongoing {category}"

            # Create new session if no recent match
            title = f"{category.capitalize()} Session"
            vec = embed_text(original_text)
            cur.execute("""
                INSERT INTO notes (user_id, title, original_text, category, embedding) 
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, title, original_text, category, vec))
            conn.commit()
            return f"🎓 Recorded background {category}"

        # 3. GENERAL MEMORIES
        else:
            vec = embed_text(original_text)
            cur.execute("""
                INSERT INTO notes (user_id, title, original_text, category, embedding) 
                VALUES (%s, %s, %s, 'background', %s)
            """, (user_id, f"Voice Memo ({emotion})", original_text, vec))
            conn.commit()
            return "✅ Background context saved."

    except Exception as e:
        conn.rollback()
        return f"Error: {str(e)}"
    finally:
        cur.close()
        conn.close()