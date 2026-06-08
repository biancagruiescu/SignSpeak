import os
import cv2
import mediapipe as mp
import pandas as pd

SPLIT_DATASET_PATH = "dataset/split"
OUTPUT_PATH = "dataset/processed"

TARGET_LABELS = ["A", "B", "C", "L", "O", "V", "W", "Y"]
SPLITS = ["train", "validation", "test"]

os.makedirs(OUTPUT_PATH, exist_ok=True)

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5
)

columns = []
for i in range(21):
    columns += [f"x{i}", f"y{i}", f"z{i}"]
columns.append("label")

for split in SPLITS:
    data = []

    print(f"\nProcessing split: {split}")

    for label in TARGET_LABELS:
        folder_path = os.path.join(SPLIT_DATASET_PATH, split, label)

        print(f"Processing {label}...")

        count = 0

        for image_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, image_name)

            image = cv2.imread(image_path)

            if image is None:
                continue

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]

                row = []

                for landmark in hand_landmarks.landmark:
                    row.append(landmark.x)
                    row.append(landmark.y)
                    row.append(landmark.z)

                row.append(label)
                data.append(row)
                count += 1

        print(f"{label}: {count} images processed")

    df = pd.DataFrame(data, columns=columns)
    df.to_csv(os.path.join(OUTPUT_PATH, f"{split}_landmarks.csv"), index=False)

print("\nLandmark extraction completed for train, validation and test.")