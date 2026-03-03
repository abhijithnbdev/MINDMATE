import psycopg2
from pgvector.psycopg2 import register_vector

PG_CONFIG = {
    "dbname": "mindmate",
    "user": "postgres",
    "password": "postgres123",
    "host": "localhost",
    "port": 5432
}

def init_db():
    conn = psycopg2.connect(**PG_CONFIG)
    register_vector(conn)
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        password_hash TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id SERIAL PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        sender TEXT,
        text TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        embedding VECTOR(384)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id SERIAL PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        title TEXT,
        content TEXT,
        embedding VECTOR(384),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        title TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print("✅ DB initialized")

if __name__ == "__main__":
    init_db()
