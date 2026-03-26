# rag/retriever.py
from services.db import get_db
from rag.embedder import embed_text

def retrieve_context(user_id: str, query: str, limit: int = 5) -> str:
    conn = get_db()
    cur = conn.cursor()

    query_vec = embed_text(query)

    cur.execute(
        """
        SELECT text, timestamp
        FROM chat_messages
        WHERE user_id = %s
          AND embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (user_id, query_vec, limit)
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return ""

    # Include timestamp so LLM CANNOT hallucinate dates
    context_lines = []
    for text, ts in rows:
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "date not recorded"
        context_lines.append(f"[{ts_str}] {text}")

    return "\n".join(context_lines)

# rag/retriever.py
from services.db import get_db
from rag.embedder import embed_text
from datetime import datetime

def retrieve_combined_context(user_id: str, query: str, limit: int = 3) -> str:
    """
    Fetches the ultimate context: 
    - Future Schedule (Events)
    - Semantic Memories (Notes)
    - Active Tasks (Reminders)
    - Recent Conversations (Chat History)
    """
    conn = get_db()
    cur = conn.cursor()
    query_vec = embed_text(query)

    # 1. Fetch Upcoming Events & Reminders (Structured)
    cur.execute("""
        SELECT message, trigger_time, priority_level 
        FROM reminders 
        WHERE user_id = %s AND status = 'active'
        ORDER BY priority ASC, trigger_time ASC LIMIT 3
    """, (user_id,))
    reminders = cur.fetchall()

    cur.execute("""
        SELECT title, start_time, location_name 
        FROM events 
        WHERE user_id = %s AND start_time >= NOW() - INTERVAL '6 hours'
        ORDER BY start_time ASC LIMIT 3
    """, (user_id,))
    events = cur.fetchall()

    # 2. Fetch Relevant Notes (Semantic Vector Search)
    cur.execute("""
        SELECT original_text, created_at 
        FROM notes 
        WHERE user_id = %s 
        ORDER BY embedding <=> %s::vector 
        LIMIT %s
    """, (user_id, query_vec, limit))
    notes = cur.fetchall()

    # 3. Fetch Past Conversations (Semantic Vector Search)
    cur.execute("""
        SELECT sender, text, created_at 
        FROM chat_messages 
        WHERE user_id = %s 
        ORDER BY embedding <=> %s::vector 
        LIMIT %s
    """, (user_id, query_vec, limit))
    chats = cur.fetchall()

    conn.close()

    # 4. Format for the Personal Assistant Persona
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context = f"CURRENT SYSTEM TIME: {now}\n\n"

    if reminders:
        context += "--- PENDING TASKS ---\n"
        for r in reminders:
            context += f"- [{r[2]}] {r[0]} due at {r[1]}\n"

    if events:
        context += "\n--- UPCOMING SCHEDULE ---\n"
        for e in events:
            context += f"- Event: {e[0]} at {e[1]} ({e[2]})\n"

    if notes:
        context += "\n--- PAST MEMORIES & NOTES ---\n"
        for n in notes:
            context += f"- Memory ({n[1].date()}): {n[0]}\n"

    if chats:
        context += "\n--- PREVIOUS RELEVANT CHATS ---\n"
        for c in chats:
            context += f"- {c[0]}: {c[1]} ({c[2].strftime('%H:%M')})\n"

    return context