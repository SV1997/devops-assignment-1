from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)

DB_NAME = os.environ.get("DB_NAME", "aceest_fitness.db")


# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            age INTEGER,
            height REAL,
            weight REAL,
            program TEXT,
            calories INTEGER,
            target_weight REAL,
            membership_status TEXT DEFAULT 'Active'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date TEXT NOT NULL,
            workout_type TEXT,
            duration_min INTEGER,
            notes TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            week TEXT,
            adherence INTEGER
        )
    """)
    conn.commit()
    conn.close()


# ---------- HEALTH ----------
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "app": "ACEest Fitness & Gym API 2"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


# ---------- CLIENTS ----------
@app.route("/clients", methods=["GET"])
def get_clients():
    conn = get_db()
    clients = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(c) for c in clients]), 200


@app.route("/clients/<int:client_id>", methods=["GET"])
def get_client(client_id):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    conn.close()
    if not client:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(dict(client)), 200


@app.route("/clients", methods=["POST"])
def add_client():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    conn = None
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO clients (name, age, height, weight, program, calories,
               target_weight, membership_status) VALUES (?,?,?,?,?,?,?,?)""",
            (
                data["name"],
                data.get("age"),
                data.get("height"),
                data.get("weight"),
                data.get("program"),
                data.get("calories"),
                data.get("target_weight"),
                data.get("membership_status", "Active"),
            ),
        )
        conn.commit()
        return jsonify({"message": f"Client '{data['name']}' added successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Client already exists"}), 409
    finally:
        if conn:
            conn.close()


@app.route("/clients/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    conn = get_db()
    existing = conn.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Client not found"}), 404
    fields = ["age", "height", "weight", "program", "calories", "target_weight", "membership_status"]
    updates = {k: data[k] for k in fields if k in data}
    if not updates:
        conn.close()
        return jsonify({"error": "No valid fields to update"}), 400
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn.execute(
        f"UPDATE clients SET {set_clause} WHERE id=?",
        (*updates.values(), client_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Client updated"}), 200


@app.route("/clients/<int:client_id>", methods=["DELETE"])
def delete_client(client_id):
    conn = get_db()
    existing = conn.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Client not found"}), 404
    conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Client deleted"}), 200


# ---------- WORKOUTS ----------
@app.route("/workouts", methods=["GET"])
def get_workouts():
    client_name = request.args.get("client")
    conn = get_db()
    if client_name:
        rows = conn.execute(
            "SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC", (client_name,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM workouts ORDER BY date DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/workouts", methods=["POST"])
def add_workout():
    data = request.get_json()
    required = ["client_name", "date", "workout_type"]
    if not data or not all(k in data for k in required):
        return jsonify({"error": "client_name, date, and workout_type are required"}), 400
    conn = get_db()
    conn.execute(
        "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?,?,?,?,?)",
        (data["client_name"], data["date"], data["workout_type"],
         data.get("duration_min", 60), data.get("notes", "")),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Workout logged"}), 201


# ---------- PROGRESS ----------
@app.route("/progress/<string:client_name>", methods=["GET"])
def get_progress(client_name):
    conn = get_db()
    rows = conn.execute(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id",
        (client_name,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/progress", methods=["POST"])
def log_progress():
    data = request.get_json()
    if not data or not data.get("client_name") or data.get("adherence") is None:
        return jsonify({"error": "client_name and adherence are required"}), 400
    conn = get_db()
    conn.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?,?,?)",
        (data["client_name"], data.get("week", ""), data["adherence"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Progress logged"}), 201


# ---------- PROGRAM GENERATOR ----------
PROGRAMS = {
    "fat_loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "muscle_gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "beginner": ["Full Body 3x/week", "Light Strength + Mobility"],
}


@app.route("/generate-program", methods=["POST"])
def generate_program():
    data = request.get_json()
    goal = (data or {}).get("goal", "beginner").lower().replace(" ", "_")
    if goal not in PROGRAMS:
        return jsonify({"error": f"Unknown goal. Choose from: {list(PROGRAMS.keys())}"}), 400
    import random
    program = random.choice(PROGRAMS[goal])
    client_name = (data or {}).get("client_name")
    if client_name:
        conn = get_db()
        conn.execute("UPDATE clients SET program=? WHERE name=?", (program, client_name))
        conn.commit()
        conn.close()
    return jsonify({"goal": goal, "program": program}), 200


# ---------- MEMBERSHIP ----------
@app.route("/membership/<int:client_id>", methods=["GET"])
def check_membership(client_id):
    conn = get_db()
    client = conn.execute(
        "SELECT name, membership_status FROM clients WHERE id=?", (client_id,)
    ).fetchone()
    conn.close()
    if not client:
        return jsonify({"error": "Client not found"}), 404
    return jsonify({"name": client["name"], "membership_status": client["membership_status"]}), 200


# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
