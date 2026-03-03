import csv
from datetime import datetime
from services.db import get_db

ACTIVITY_MAP = {
    "Sleep": 0,
    "Breakfast": 1,
    "Study": 2,
    "Work": 3,
    "Rest": 4,
    "Gym": 5,
    "Lunch": 6,
    "Dinner": 7
}

CSV_PATH = "models/global_training_data.csv"

def extract_activity(title: str):
    t = title.lower()
    if "sleep" in t: return "Sleep"
    if "breakfast" in t: return "Breakfast"
    if "lunch" in t: return "Lunch"
    if "dinner" in t: return "Dinner"
    if "gym" in t: return "Gym"
    if "study" in t or "class" in t: return "Study"
    if "work" in t or "office" in t: return "Work"
    return None

def main():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, start_time
        FROM events
        WHERE start_time IS NOT NULL
    """)

    rows = cur.fetchall()
    conn.close()

    new_rows = []

    prev_activity = 0

    for title, start in rows:
        activity = extract_activity(title)
        if not activity:
            continue

        dt = start if isinstance(start, datetime) else datetime.fromisoformat(start)

        new_rows.append([
            dt.hour,
            dt.weekday(),
            dt.month,
            prev_activity,
            activity
        ])

        prev_activity = ACTIVITY_MAP.get(activity, 0)

    if not new_rows:
        print("No new training data")
        return

    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    print(f"Appended {len(new_rows)} rows")

if __name__ == "__main__":
    main()
