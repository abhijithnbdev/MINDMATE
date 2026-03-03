# services/analytics.py
from services.db import get_db, get_cursor
from datetime import datetime, timedelta

def get_daily_summary(user_id: str):
    conn = get_db()
    cur = get_cursor(conn) # Use RealDictCursor
    
    try:
        # Use Postgres date casting for accuracy
        cur.execute("""
            SELECT title, category, start_time 
            FROM events 
            WHERE user_id = %s 
            AND start_time::date = CURRENT_DATE
            ORDER BY start_time ASC
        """, (user_id,))
        
        events = cur.fetchall()
        
        if not events:
            return {"date": str(datetime.now().date()), "event_count": 0, "timeline": []}

        categories = {}
        timeline = []
        
        for row in events:
            # Safe access thanks to RealDictCursor
            title = row['title']
            cat = row['category'] or "Uncategorized"
            start_time = str(row['start_time'])

            time_str = start_time.split(' ')[1][:5] if ' ' in start_time else start_time
            timeline.append(f"{time_str} - {title}")
            categories[cat] = categories.get(cat, 0) + 1

        top_cat = max(categories, key=categories.get) if categories else "None"
        
        return {
            "event_count": len(events),
            "top_category": top_cat,
            "timeline": timeline
        }
    finally:
        conn.close()

def get_period_stats(user_id: str, start_date: str, end_date: str):
    """
    Returns total hours per category between start_date and end_date (inclusive).
    """
    conn = get_db()
    conn.row_factory = None
    cur = conn.cursor()

    cur.execute(
        """
        SELECT category, start_time, end_time
        FROM events
        WHERE user_id = ?
          AND date(start_time) BETWEEN ? AND ?
        """,
        (user_id, start_date, end_date),
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {}

    stats = {}
    for row in rows:
        try:
            category = row["category"]
            start_time = row["start_time"]
            end_time = row["end_time"]
        except TypeError:
            category = row[0]
            start_time = row[1]
            end_time = row[2]

        if not category:
            category = "Uncategorized"

        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

        if end_time:
            try:
                end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except Exception:
                end_dt = start_dt + timedelta(hours=1)
        else:
            end_dt = start_dt + timedelta(hours=1)

        hours = max((end_dt - start_dt).total_seconds() / 3600.0, 0.25)
        stats[category] = stats.get(category, 0.0) + hours

    return stats
