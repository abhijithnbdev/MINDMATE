import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

def train_user_model(user_id):
    base_path = os.path.dirname(__file__)
    csv_path = os.path.join(base_path, "users", f"{user_id}_data.csv")
    
    if not os.path.exists(csv_path):
        print("❌ CSV not found. Run prepare_data.py first.")
        return

    df = pd.read_csv(csv_path)

    # 1. Encode Activity Titles (e.g., 'Deep Work' -> 5)
    le = LabelEncoder()
    df['Target'] = le.fit_transform(df['title'])

    # 2. Define Features (X) and Target (y)
    X = df[['Hour', 'DayOfWeek', 'Month']]
    y = df['Target']

    # 3. Train Random Forest (High Accuracy for small datasets)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # 4. Save both Model and Encoder as a dictionary
    model_data = {
        "model": model,
        "encoder": le
    }
    
    model_path = os.path.join(base_path, "users", f"{user_id}.pkl")
    joblib.dump(model_data, model_path)
    print(f"🚀 High-accuracy model saved to: {model_path}")

if __name__ == "__main__":
    train_user_model("meanonymus87@gmail.com")