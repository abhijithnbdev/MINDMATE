import os
import glob
import asyncio
# CHANGE THIS LINE:
from models.train_user_habit_model import train_user_model 

async def run_weekly_retraining():
    print("🚀 Starting Weekly Synapse Refresh for all users...")
    
    tokens_path = os.path.join(os.path.dirname(__file__), "..", "tokens", "token_*.pickle")
    token_files = glob.glob(tokens_path)

    for file_path in token_files:
        try:
            filename = os.path.basename(file_path)
            user_email = filename.replace("token_", "").replace(".pickle", "")
            
            print(f"⚙️ Retraining HabitEngine for: {user_email}")
            
            # CHANGE THIS LINE TOO:
            train_user_model(user_email) 
            
        except Exception as e:
            print(f"❌ Failed to train model for {user_email}: {e}")

    print("✅ Weekly training cycle complete.")