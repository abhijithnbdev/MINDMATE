# rag/memory_writer.py
from services.db import get_db
from rag.embedder import embed_text

def store_chat(user_id: str, sender: str, text: str):
    conn = get_db()
    cur = conn.cursor()

    embedding = embed_text(text)

    cur.execute("""
        INSERT INTO chat_messages (user_id, sender, text, embedding)
        VALUES (%s, %s, %s, %s)
    """, (user_id, sender, text, embedding))

    conn.commit()
    conn.close()
