import joblib
import os
import numpy as np
from datetime import datetime

class MindMateModel:
    def __init__(self):
        self.model = None
        self.activity_map = {'Sleep': 0, 'Breakfast': 1, 'Study': 2, 'Work': 3, 'Rest': 4, 'Gym': 5}
        self.location_map = {'Home': 0, 'Office': 1, 'Library': 2, 'Transit': 3}
        self.fatigue_map = {'Low': 0, 'Medium': 1, 'High': 2}
        self.reverse_activity_map = {v: k for k, v in self.activity_map.items()}
        self._load_models()

    def _load_models(self):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_path, "models", "habit_model.pkl")
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print(f"✅ ML Brain loaded: {model_path}")
            else:
                print("⚠️ ML Model file not found.")
        except Exception as e:
            print(f"❌ Error loading model: {e}")

    def predict_single(self, hour, day_of_week, prev_activity, location="Home", fatigue="Low"):
        if not self.model: return "Rest"
        X = [[np.sin(2*np.pi*hour/24), np.cos(2*np.pi*hour/24), day_of_week, 
              self.activity_map.get(prev_activity, 4), self.location_map.get(location, 0), 
              self.fatigue_map.get(fatigue, 0)]]
        try:
            return self.reverse_activity_map.get(self.model.predict(X)[0], "Rest")
        except:
            return "Rest"