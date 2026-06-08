import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import joblib

# 1. Încărcăm modelul
model = joblib.load("models/asl_random_forest_model.pkl")

# 2. Generăm numele coloanelor fix ca la antrenare (x0, y0, z0... x20, y20, z20)
feature_names = []
for i in range(21):
    feature_names += [f"x{i}", f"y{i}", f"z{i}"]

# 3. Inițializăm MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()
    if not success:
        break

    # Efect de oglindă pentru a fi mai natural pentru utilizator
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    display_text = "Se cauta o mana..."

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Desenăm punctele pe mână
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            row = []
            for landmark in hand_landmarks.landmark:
                row.append(landmark.x)
                row.append(landmark.y)
                row.append(landmark.z)

        
            input_data = pd.DataFrame([row], columns=feature_names)

            # Facem predictia
            prediction = model.predict(input_data)
            predicted_label = prediction[0]

            # Calcul probabilitatea 
            probabilities = model.predict_proba(input_data)
            confidence = np.max(probabilities) * 100

            # Format textul care va aparea pe ecran
            display_text = f"Predictie: {predicted_label} ({confidence:.1f}%)"

    # Afisam textul pe ecran
    cv2.putText(
        frame,
        display_text,
        (10, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0) if "Predictie" in display_text else (0, 165, 255),
        2
    )

    cv2.imshow("ASL Real-Time Prediction", frame)

    # Apasă 'q' pentru a închide fereastra
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()