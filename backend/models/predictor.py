import os
import joblib
import pandas as pd

class HabitEngine:
    def __init__(self, user_id: str):
        self.model = None
        self.encoder = None
        
        # Path to: backend/models/users/meanonymus87@gmail.com.pkl
        model_path = os.path.join(os.path.dirname(__file__), "users", f"{user_id}.pkl")

        if os.path.exists(model_path):
            try:
                data = joblib.load(model_path)
                # Load the dictionary saved by the trainer
                if isinstance(data, dict):
                    self.model = data.get('model')
                    self.encoder = data.get('encoder')
                else:
                    self.model = data
            except Exception as e:
                print(f"❌ Error loading model: {e}")

    def predict(self, hour, day, month):
        # 🟢 Fallback for night hours if model isn't trained on Sleep
        if hour < 7 or hour > 23:
            return "Sleep"

        if not self.model:
            return "Rest"

        try:
            # Predict using exact column names from training
            df = pd.DataFrame([[hour, day, month]], columns=["Hour", "DayOfWeek", "Month"])
            pred_id = self.model.predict(df)[0]
            
            # 🟢 Decode the number back to the string (e.g., 5 -> 'Deep Work')
            if self.encoder:
                return self.encoder.inverse_transform([pred_id])[0]
            return str(pred_id)
            
        except Exception as e:
            return "Routine Activity"