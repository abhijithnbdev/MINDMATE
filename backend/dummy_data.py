import psycopg2
from datetime import datetime, timedelta
import random
from services.db import get_db

def insert_dummy_data(user_id):
    conn = get_db()
    cur = conn.cursor()
    
    activities = [
        ("Morning Exercise", 7, 8, "Gym"),
        ("Deep Work/Coding", 9, 13, "Home Office"),
        ("Lunch Break", 13, 14, "Cafe"),
        ("Team Meeting", 14, 15, "Office"),
        ("Skill Learning", 16, 18, "Library"),
        ("Evening Walk", 19, 20, "Park"),
        ("Dinner & Relax", 20, 22, "Home")
    ]

    # Generate data for the last 20 days to reach ~100 entries
    current_date = datetime.now()
    count = 0

    try:
        for day in range(20):
            date_to_insert = current_date - timedelta(days=day)
            
            for title, start_h, end_h, loc in activities:
                start_time = date_to_insert.replace(hour=start_h, minute=0, second=0)
                
                cur.execute("""
                    INSERT INTO events (user_id, title, start_time, location_name, origin_location)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, title, start_time, loc, "Dummy Generator"))
                count += 1

        conn.commit()
        print(f"✅ Successfully inserted {count} dummy events for {user_id}")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    insert_dummy_data("meanonymus87@gmail.com")