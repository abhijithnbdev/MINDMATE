import pandas as pd
import os
import sys
# Add parent directory to path to find services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.db import get_db

def export_to_csv(user_id):
    conn = get_db()
    # 🟢 Pulling title and start_time to learn temporal habits
    query = "SELECT title, start_time FROM events WHERE user_id = %s"
    df = pd.read_sql(query, conn, params=(user_id,))
    
    if df.empty:
        print(f"❌ No data found for {user_id}. Log some habits first!")
        return

    # 🟢 Feature Engineering
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['Hour'] = df['start_time'].dt.hour
    df['DayOfWeek'] = df['start_time'].dt.weekday
    df['Month'] = df['start_time'].dt.month
    
    # 🟢 Save CSV in the users folder
    csv_path = os.path.join(os.path.dirname(__file__), "users", f"{user_id}_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"✅ Created training CSV at: {csv_path}")
    conn.close()

if __name__ == "__main__":
    export_to_csv("meanonymus87@gmail.com")