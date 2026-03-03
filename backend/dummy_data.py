# dummy_data.py
import random
from datetime import datetime, timedelta
from services.db import get_db
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

USERS = [
    {"user_id": "dummy_professional", "role": "professional"},
    {"user_id": "dummy_student", "role": "student"},
]

DUMMY_PASSWORD_HASH = "__dummy__"  # matches your migration logic

# ---------------- USERS ----------------
def ensure_user(cur, user_id):
    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    if not cur.fetchone():
        cur.execute(
            """
            INSERT INTO users (user_id, password_hash)
            VALUES (%s, %s)
            """,
            (user_id, DUMMY_PASSWORD_HASH),
        )

# ---------------- EVENTS ----------------
def insert_event(cur, user_id, title, start, end):
    cur.execute(
        """
        INSERT INTO events (user_id, title, category, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, title, "personal", start, end),
    )

# ---------------- CHAT (RAG MEMORY) ----------------
def insert_chat(cur, user_id, text):
    vec = model.encode(text).tolist()
    cur.execute(
        """
        INSERT INTO chat_messages (user_id, sender, text, embedding)
        VALUES (%s, %s, %s, %s)
        """,
        (user_id, "user", text, vec),
    )

# ---------------- DAY GENERATORS ----------------
def generate_professional_day(cur, user_id, date):
    insert_event(cur, user_id, "Office Work", date.replace(hour=9), date.replace(hour=13))
    insert_event(cur, user_id, "Office Work", date.replace(hour=14), date.replace(hour=18))

    if random.random() > 0.6:
        insert_event(cur, user_id, "Gym", date.replace(hour=18), date.replace(hour=19))

    insert_chat(cur, user_id, "Worked on project milestones today")
    insert_chat(cur, user_id, "Client meeting about system design")

def generate_student_day(cur, user_id, date):
    insert_event(cur, user_id, "Classes", date.replace(hour=9), date.replace(hour=13))
    insert_event(cur, user_id, "Self Study", date.replace(hour=15), date.replace(hour=18))

    insert_chat(cur, user_id, "Studied operating systems")
    insert_chat(cur, user_id, "Preparing for upcoming exams")

# ---------------- MAIN ----------------
def main():
    conn = get_db()
    cur = conn.cursor()

    for u in USERS:
        ensure_user(cur, u["user_id"])

        for i in range(90):  # 90 days history
            day = datetime.now() - timedelta(days=i)

            if u["role"] == "professional":
                generate_professional_day(cur, u["user_id"], day)
            else:
                generate_student_day(cur, u["user_id"], day)

    conn.commit()
    conn.close()
    print("✅ Dummy users + realistic historical data inserted into PostgreSQL")

if __name__ == "__main__":
    main()
