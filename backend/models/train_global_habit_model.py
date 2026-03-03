# models/train_global_habit_model.py
import pandas as pd, joblib
from sklearn.ensemble import RandomForestClassifier

CSV = "models/global/training_data_global.csv"
OUT = "models/global/habit_model_global.pkl"

df = pd.read_csv(CSV)

X = df[["Hour", "DayOfWeek", "Month"]]
y = df["Activity"]

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42
)
model.fit(X, y)

joblib.dump(model, OUT)
print("✅ Global model trained")
