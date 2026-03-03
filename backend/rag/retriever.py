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

def retrieve_combined_context(user_id: str, query: str) -> str:
    """
    Fetches context from both Events (structured) and Notes (semantic).
    """
    conn = get_db()
    cur = conn.cursor()
    
    # 1. Fetch relevant Events (Structured Search)
    cur.execute("""
        SELECT title, start_time, location_name 
        FROM events 
        WHERE user_id = %s AND start_time >= NOW() - INTERVAL '1 day'
        ORDER BY start_time ASC LIMIT 3
    """, (user_id,))
    events = cur.fetchall()
    
    # 2. Fetch relevant Notes (Semantic Vector Search)
    query_vec = embed_text(query)
    cur.execute("""
        SELECT original_text 
        FROM notes 
        WHERE user_id = %s 
        ORDER BY embedding <=> %s::vector 
        LIMIT 3
    """, (user_id, query_vec))
    notes = cur.fetchall()
    conn.close()

    # 3. Format the result for Phi-3
    context = "--- RELEVANT SCHEDULE ---\n"
    for e in events:
        context += f"Event: {e[0]} at {e[1]} in {e[2]}\n"
    
    context += "\n--- RELEVANT MEMORIES ---\n"
    for n in notes:
        context += f"Note: {n[0]}\n"
        
    return context