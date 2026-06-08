from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import cv2
import numpy as np
import joblib
import mediapipe as mp
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
CORS(app)


# ==========================
# FRONTEND ROUTES
# ==========================
@app.route("/")
def home():
    return send_from_directory("html", "index.html")


@app.route("/<page>")
def serve_html(page):
    if page.endswith(".html"):
        return send_from_directory("html", page)
    return "Not found", 404


@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory("css", filename)


@app.route("/scripts/<path:filename>")
def serve_scripts(filename):
    return send_from_directory("scripts", filename)


@app.route("/images/<path:filename>")
def serve_images(filename):
    return send_from_directory("images", filename)


# ==========================
# DATABASE
# ==========================
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            input_text TEXT,
            translated_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ==========================
# ML MODEL
# ==========================
model = joblib.load("models/asl_random_forest_model.pkl")

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def get_feature_names():
    names = []

    for i in range(21):
        names += [f"x{i}", f"y{i}", f"z{i}"]

    return names


# ==========================
# SIGN UP
# ==========================
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "Account created successfully!"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400


# ==========================
# LOGIN / SIGNIN
# ==========================
@app.route("/login", methods=["POST"])
@app.route("/signin", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "Invalid email or password"}), 401

    stored_password = user["password"]
    valid_password = False

    try:
        valid_password = check_password_hash(stored_password, password)
    except Exception:
        valid_password = False
    # Compatibilitate pentru conturile vechi salvate cu parola în clar
    if not valid_password and stored_password == password:
        valid_password = True

        new_hash = generate_password_hash(password, method="pbkdf2:sha256")
        cursor.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (new_hash, user["id"])
        )
        conn.commit()

    conn.close()

    if valid_password:
        return jsonify({
            "message": "Login successful!",
            "email": user["email"],
            "username": user["username"]
        })
    return jsonify({"error": "Invalid email or password"}), 401


# ==========================
# USER PROFILE
# ==========================
@app.route("/user/<email>", methods=["GET"])
def get_user(email):
    email = email.strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("""
        SELECT input_text, translated_text, created_at
        FROM translations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user["id"],))

    rows = cursor.fetchall()
    conn.close()

    history = []

    for row in rows:
        history.append({
            "input_text": row["input_text"],
            "translated_text": row["translated_text"],
            "created_at": row["created_at"],
            "timestamp": row["created_at"]
        })

    return jsonify({
        "username": user["username"],
        "email": user["email"],
        "history": history
    })


# ==========================
# HISTORY
# Pentru scripts.js dacă folosește /history/<email>
# ==========================
@app.route("/history/<email>", methods=["GET"])
def get_history(email):
    email = email.strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("""
        SELECT input_text, translated_text, created_at
        FROM translations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user["id"],))

    rows = cursor.fetchall()
    conn.close()

    history = []

    for row in rows:
        history.append({
            "input_text": row["input_text"],
            "translated_text": row["translated_text"],
            "created_at": row["created_at"],
            "timestamp": row["created_at"]
        })

    return jsonify(history)


# ==========================
# PREDICT SIGN
# ==========================
@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"prediction": "-", "confidence": 0.0})

    file = request.files["image"]

    image_bytes = file.read()
    npimg = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({"prediction": "-", "confidence": 0.0})

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if not results.multi_hand_landmarks:
        return jsonify({"prediction": "-", "confidence": 0.0})

    hand_landmarks = results.multi_hand_landmarks[0]

    row = []

    for landmark in hand_landmarks.landmark:
        row.append(landmark.x)
        row.append(landmark.y)
        row.append(landmark.z)

    input_data = pd.DataFrame([row], columns=get_feature_names())

    prediction = model.predict(input_data)[0]

    confidence = 0.0

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(input_data)[0]
        confidence = float(np.max(probabilities))

    return jsonify({
        "prediction": str(prediction),
        "confidence": confidence
    })


# ==========================
# SAVE PREDICTION HISTORY
# ==========================
@app.route("/save_translation", methods=["POST"])
def save_translation():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    input_text = data.get("input_text", "Camera input")
    translated_text = data.get("translated_text")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    if not translated_text:
        return jsonify({"error": "Prediction is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("""
        INSERT INTO translations (user_id, input_text, translated_text)
        VALUES (?, ?, ?)
    """, (user["id"], input_text, translated_text))

    conn.commit()
    conn.close()

    return jsonify({"message": "Prediction saved successfully!"})


# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    init_db()
app.run(host="0.0.0.0", port=5000)