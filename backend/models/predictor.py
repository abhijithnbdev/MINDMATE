import os
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
GLOBAL_MODEL = os.path.join(BASE_DIR, "global", "habit_model_global.pkl")

class HabitEngine:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.activity_map = {
            0: "Sleep",
            1: "Breakfast",
            2: "Study",
            3: "Work",
            4: "Rest",
            5: "Gym",
            6: "Snack"
        }

        user_model = os.path.join(
            BASE_DIR, "users", user_id, "habit_model.pkl"
        )

        if os.path.exists(user_model):
            self.model = joblib.load(user_model)
            self.source = "user"
        else:
            self.model = joblib.load(GLOBAL_MODEL)
            self.source = "global"

    def predict(self, hour, day, month, prev=0):
        df = pd.DataFrame([[hour, day, month, prev]],
            columns=["Hour", "DayOfWeek", "Month", "PrevActivity"]
        )
        pred = int(self.model.predict(df)[0])
        return self.activity_map.get(pred, "Rest")
