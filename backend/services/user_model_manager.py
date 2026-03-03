# services/user_model_manager.py
import os
from models.predictor import HabitEngine

BASE = "models"

def get_habit_engine(user_id: str) -> HabitEngine:
    user_model = f"{BASE}/users/{user_id}/habit_model.pkl"
    global_model = f"{BASE}/global/habit_model_global.pkl"

    if os.path.exists(user_model):
        return HabitEngine(user_model)

    if os.path.exists(global_model):
        return HabitEngine(global_model)

    return HabitEngine(None)  # fallback
