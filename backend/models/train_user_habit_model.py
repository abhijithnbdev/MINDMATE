import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

BASE = os.path.dirname(__file__)

def train_for_user(user_id: str):
    user_dir = os.path.join(BASE, "users", user_id)
    csv_path = os.path.join(user_dir, "training_data.csv")
    model_path = os.path.join(user_dir, "habit_model.pkl")

    if not os.path.exists(csv_path):
        return False

    df = pd.read_csv(csv_path)

    X = df[["Hour", "DayOfWeek", "Month", "PrevActivity"]]
    y = df["Activity"]

    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)

    joblib.dump(model, model_path)
    return True
