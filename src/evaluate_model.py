import os
import pandas as pd
import joblib
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

TEST_PATH = "dataset/processed/test_landmarks.csv"
MODEL_PATH = "models/asl_random_forest_model.pkl"
OUTPUT_DIR = "thesis_assets"

os.makedirs(OUTPUT_DIR, exist_ok=True)

test_df = pd.read_csv(TEST_PATH)

X_test = test_df.drop("label", axis=1)
y_test = test_df["label"]

model = joblib.load(MODEL_PATH)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
report = classification_report(y_test, predictions)

print("Test Accuracy:", accuracy)
print("\nClassification Report:")
print(report)

with open(os.path.join(OUTPUT_DIR, "classification_report.txt"), "w") as file:
    file.write(f"Test Accuracy: {accuracy}\n\n")
    file.write(report)

labels = sorted(y_test.unique())
cm = confusion_matrix(y_test, predictions, labels=labels)

display = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
display.plot(values_format="d")

plt.title("Confusion Matrix - ASL Sign Recognition")
plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix.png"), dpi=300, bbox_inches="tight")
plt.close()

print("\nEvaluation files saved in thesis_assets/")