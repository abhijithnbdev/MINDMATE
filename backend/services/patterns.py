# services/patterns.py
from services.db import get_db, get_cursor
from collections import Counter

def daily_overview(user_id: str):
    conn = get_db()
    cur = get_cursor(conn)

    cur.execute("SELECT start_time, title FROM events WHERE user_id = %s", (user_id,))
    rows = cur.fetchall()
    conn.close()

    buckets = {"morning": [], "afternoon": [], "evening": [], "night": []}

    for row in rows:
        # Assuming start_time is ISO format like "2025-12-18 08:30"
        try:
            time_part = row["start_time"].split(" ")[1] # Get HH:MM
            hour = int(time_part.split(":")[0])
            activity = row["title"]

            if 5 <= hour < 12:   buckets["morning"].append(activity)
            elif 12 <= hour < 17: buckets["afternoon"].append(activity)
            elif 17 <= hour < 21: buckets["evening"].append(activity)
            else:                 buckets["night"].append(activity)
        except:
            continue

    result = {}
    for period, acts in buckets.items():
        if acts:
            common = Counter(acts).most_common(1)[0]
            result[period] = {
                "dominant_activity": common[0],
                "consistency": round(common[1] / len(acts), 2)
            }
        else:
            result[period] = {"dominant_activity": "Rest", "consistency": 0.0}

    return result