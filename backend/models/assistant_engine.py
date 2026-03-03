import joblib
import pandas as pd
from datetime import datetime

class AI_Assistant:
    def __init__(self, model_path):
        self.model = joblib.load(model_path)

    def predict_day(self, date_str):
        date = datetime.fromisoformat(date_str)
        data = []

        for hour in range(24):
            X = pd.DataFrame([[hour, date.weekday()]], columns=["hour", "day"])
            pred = self.model.predict(X)[0]
            data.append((f"{hour:02d}:00", pred))

        return data
