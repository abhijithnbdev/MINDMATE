import sqlite3
import psycopg2
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime

# ---------- PATHS ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DB = os.path.join(BASE_DIR, "db", "mindmate.db")

PG_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "mindmate",
    "user": "mindmate_user",
    "password": "mindmate123"
}


model = SentenceTransformer("all-MiniLM-L6-v2")

print("SQLite DB exists:", os.path.exists(SQLITE_DB))
print("SQLite DB path:", SQLITE_DB)

# ---------- CONNECTIONS ----------
s_conn = sqlite3.connect(SQLITE_DB)
s_conn.row_factory = sqlite3.Row
s_cur = s_conn.cursor()

p_conn = psycopg2.connect(**PG_CONFIG)
p_cur = p_conn.cursor()

# ---------- HELPERS ----------
def ensure_user_exists(user_id):
    p_cur.execute(
        "INSERT INTO users (user_id, password_hash) VALUES (%s, %s) "
        "ON CONFLICT (user_id) DO NOTHING",
        (user_id, "__migrated__")
    )

def safe_timestamp(value):
    if not value:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value.upper() == "YYYY-MM-DD HH:MM:SS":
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
    return value

# ---------- USERS ----------
print("▶ Migrating users...")
s_cur.execute("SELECT * FROM users")
for r in s_cur.fetchall():
    p_cur.execute(
        "INSERT INTO users (user_id, password_hash) VALUES (%s,%s) "
        "ON CONFLICT (user_id) DO NOTHING",
        (r["user_id"], r["password"])
    )

# ---------- EVENTS ----------
print("▶ Migrating events...")
s_cur.execute("""
    SELECT
        id,
        user_id,
        title,
        category,
        start_time,
        end_time,
        location_name,
        origin_location
    FROM events
""")

for r in s_cur.fetchall():
    ensure_user_exists(r["user_id"])

    p_cur.execute("""
        INSERT INTO events (
            id, user_id, title, category,
            start_time, end_time,
            location_name, origin_location
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (
        r["id"],
        r["user_id"],
        r["title"],
        r["category"],
        safe_timestamp(r["start_time"]),
        safe_timestamp(r["end_time"]),
        r["location_name"],
        r["origin_location"]
    ))

# ---------- CHAT_MESSAGES ----------
print("▶ Migrating chat_messages...")
s_cur.execute("SELECT * FROM chat_messages")
for r in s_cur.fetchall():
    ensure_user_exists(r["user_id"])
    text = r["text"] or ""
    vec = model.encode(text).tolist()

    p_cur.execute("""
        INSERT INTO chat_messages (
            user_id, sender, text, location, timestamp, embedding
        )
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        r["user_id"],
        r["sender"],
        text,
        r["location"],
        safe_timestamp(r["timestamp"]),
        vec
    ))

# ---------- MEMORIES ----------
print("▶ Migrating memories...")
s_cur.execute("SELECT * FROM memories")
for r in s_cur.fetchall():
    ensure_user_exists(r["user_id"])

    p_cur.execute("""
        INSERT INTO memories (
            id, user_id, memory_type, title,
            content, confidence_score,
            created_at, last_reinforced
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (
        r["id"],
        r["user_id"],
        r["memory_type"],
        r["title"],
        r["content"],
        r["confidence_score"],
        safe_timestamp(r["created_at"]),
        safe_timestamp(r["last_reinforced"])
    ))

# ---------- REMINDERS ----------
print("▶ Migrating reminders...")
s_cur.execute("SELECT * FROM reminders")
for r in s_cur.fetchall():
    ensure_user_exists(r["user_id"])

    p_cur.execute("""
        INSERT INTO reminders (
            id, user_id, event_id, message,
            trigger_time, status,
            recurrence_rule, priority_level
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (
        r["id"],
        r["user_id"],
        r["event_id"],
        r["message"],
        safe_timestamp(r["trigger_time"]),
        r["status"],
        r["recurrence_rule"],
        r["priority_level"]
    ))

# ---------- VOICE_ANALYSIS ----------
print("▶ Migrating voice_analysis...")
s_cur.execute("SELECT * FROM voice_analysis")
for r in s_cur.fetchall():
    ensure_user_exists(r["user_id"])

    p_cur.execute("""
        INSERT INTO voice_analysis (
            id, user_id, associated_event_id,
            original_transcript, emotion_label, stress_level
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (
        r["id"],
        r["user_id"],
        r["associated_event_id"],
        r["original_transcript"],
        r["emotion_label"],
        r["stress_level"]
    ))

# ---------- COMMIT ----------
p_conn.commit()
s_conn.close()
p_conn.close()

print("✅ MIGRATION COMPLETE — SQLite → PostgreSQL successful.")
