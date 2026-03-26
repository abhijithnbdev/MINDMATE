import psycopg2
from main import PG_CONFIG # Imports your config

try:
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT current_database(), current_user;")
    db, user = cur.fetchone()
    print(f"🚀 Success! Connected to Database: {db} as User: {user}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection Failed: {e}")