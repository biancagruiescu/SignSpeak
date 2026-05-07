from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # 🔥 IMPORTANT

# ---------------- DB ----------------
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
            input_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- TEST ----------------
@app.route("/")
def home():
    return "SignSpeak backend running"

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    print("SIGNUP:", data)

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not username or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )

        conn.commit()
        conn.close()

        print("USER INSERTED")
        return jsonify({"message": "Account created"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    print("LOGIN:", data)

    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

# ---------------- USER PAGE ----------------
@app.route("/user/<email>", methods=["GET"])
def get_user(email):
    print("USER REQUEST:", email)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("""
        SELECT input_text, translated_text
        FROM translations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user["id"],))

    translations = cursor.fetchall()
    conn.close()

    history = []
    for t in translations:
        history.append({
            "input_text": t["input_text"],
            "translated_text": t["translated_text"]
        })

    return jsonify({
        "username": user["username"],
        "email": user["email"],
        "history": history
    })

# ---------------- TEST HISTORY ----------------
@app.route("/add-test-history/<email>")
def add_test(email):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute("""
        INSERT INTO translations (user_id, input_text, translated_text)
        VALUES (?, ?, ?)
    """, (user["id"], "hello", "H E L L O"))

    conn.commit()
    conn.close()

    return jsonify({"message": "Test added"})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)