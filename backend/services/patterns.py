# services/patterns.py
from services.db import get_db, get_cursor
from collections import Counter


def analyze_user_patterns(rows):
    buckets = {"morning": [], "afternoon": [], "evening": [], "night": []}
    
    for row in rows:
        try:
            # Handle both string and datetime objects
            time_data = row["start_time"]
            if hasattr(time_data, 'hour'):
                hour = time_data.hour
            else:
                # Assuming format "YYYY-MM-DD HH:MM:SS" or similar
                time_part = str(time_data).split(" ")[1]
                hour = int(time_part.split(":")[0])
            
            activity = row["title"]

            if 5 <= hour < 12:    buckets["morning"].append(activity)
            elif 12 <= hour < 17:  buckets["afternoon"].append(activity)
            elif 17 <= hour < 21:  buckets["evening"].append(activity)
            else:                  buckets["night"].append(activity)
        except Exception as e:
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