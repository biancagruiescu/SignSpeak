import os
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

TRAIN_PATH = "dataset/processed/train_landmarks.csv"
VAL_PATH = "dataset/processed/validation_landmarks.csv"

train_df = pd.read_csv(TRAIN_PATH)
val_df = pd.read_csv(VAL_PATH)

X_train = train_df.drop("label", axis=1)
y_train = train_df["label"]

X_val = val_df.drop("label", axis=1)
y_val = val_df["label"]

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)

val_predictions = model.predict(X_val)

print("Validation Accuracy:", accuracy_score(y_val, val_predictions))
print("\nValidation Classification Report:")
print(classification_report(y_val, val_predictions))

os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/asl_random_forest_model.pkl")

print("\nModel saved in models/asl_random_forest_model.pkl")