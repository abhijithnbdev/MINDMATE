import os
import pickle
from models.predictor import HabitEngine

# 🟢 Get the absolute path to the backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 🟢 Points to: backend/models/users/
MODEL_DIR = os.path.join(BASE_DIR, "models", "users")

def get_habit_engine(user_id: str) -> HabitEngine:
    # 🟢 Path to your specific model: meanonymus87@gmail.com.pkl
    user_model_path = os.path.join(MODEL_DIR, f"{user_id}.pkl")
    
    # Global fallback path
    global_model_path = os.path.join(BASE_DIR, "models", "global", "habit_model_global.pkl")

    print(f"🔍 Checking for model at: {user_model_path}")

    if os.path.exists(user_model_path):
        print(f"✅ Found user-specific model for {user_id}")
        return HabitEngine(user_model_path)

    if os.path.exists(global_model_path):
        print(f"⚠️ User model not found. Using Global fallback.")
        return HabitEngine(global_model_path)

    print("❌ No models found. Using empty fallback.")
    return HabitEngine(None)