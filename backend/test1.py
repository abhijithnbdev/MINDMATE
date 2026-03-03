import psycopg2

try:
    conn = psycopg2.connect(
        dbname="mindmate",
        user="mindmate_user",
        password="mindmate123",
        host="127.0.0.1",
        port=5432
    )
    print("✅ psycopg2 login SUCCESS")
    conn.close()
except Exception as e:
    print("❌ psycopg2 login FAILED")
    print(e)
