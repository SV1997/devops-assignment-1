"""
test_app.py — Pytest suite for ACEest Fitness & Gym Flask API
"""
import os
import pytest

# Use in-memory SQLite so tests never touch a real file
os.environ["DB_NAME"] = ":memory:"

from app import app, init_db, get_db   # noqa: E402


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before every single test."""
    init_db()
    yield


@pytest.fixture
def client():
    """Fresh test client for every test."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── Health / Index ────────────────────────────────────────────────────────────

def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "ACEest" in data["app"]


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"


# ── Clients — CREATE ──────────────────────────────────────────────────────────

def test_add_client(client):
    res = client.post("/clients", json={"name": "Alice", "age": 28, "weight": 65.0})
    assert res.status_code == 201
    assert "Alice" in res.get_json()["message"]


def test_add_client_missing_name(client):
    res = client.post("/clients", json={"age": 30})
    assert res.status_code == 400


def test_add_client_no_body(client):
    res = client.post("/clients", json={})
    assert res.status_code == 400


def test_add_duplicate_client(client):
    client.post("/clients", json={"name": "Bob"})
    res = client.post("/clients", json={"name": "Bob"})
    assert res.status_code == 409


# ── Clients — READ ────────────────────────────────────────────────────────────

def test_get_clients_empty(client):
    res = client.get("/clients")
    assert res.status_code == 200
    assert res.get_json() == []


def test_get_clients(client):
    client.post("/clients", json={"name": "Carol"})
    res = client.get("/clients")
    assert res.status_code == 200
    names = [c["name"] for c in res.get_json()]
    assert "Carol" in names


def test_get_client_by_id(client):
    client.post("/clients", json={"name": "Dave", "age": 35})
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.get(f"/clients/{cid}")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Dave"


def test_get_client_not_found(client):
    res = client.get("/clients/9999")
    assert res.status_code == 404


# ── Clients — UPDATE ──────────────────────────────────────────────────────────

def test_update_client(client):
    client.post("/clients", json={"name": "Eve"})
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.put(f"/clients/{cid}", json={"age": 30, "weight": 58.0})
    assert res.status_code == 200
    updated = client.get(f"/clients/{cid}").get_json()
    assert updated["age"] == 30
    assert updated["weight"] == 58.0


def test_update_client_not_found(client):
    res = client.put("/clients/9999", json={"age": 25})
    assert res.status_code == 404


def test_update_client_no_valid_fields(client):
    client.post("/clients", json={"name": "Frank"})
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.put(f"/clients/{cid}", json={"nonexistent_field": "xyz"})
    assert res.status_code == 400


def test_update_membership_status(client):
    client.post("/clients", json={"name": "Grace", "membership_status": "Active"})
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.put(f"/clients/{cid}", json={"membership_status": "Expired"})
    assert res.status_code == 200
    assert client.get(f"/clients/{cid}").get_json()["membership_status"] == "Expired"


# ── Clients — DELETE ──────────────────────────────────────────────────────────

def test_delete_client(client):
    client.post("/clients", json={"name": "Hank"})
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.delete(f"/clients/{cid}")
    assert res.status_code == 200
    assert client.get(f"/clients/{cid}").status_code == 404


def test_delete_client_not_found(client):
    res = client.delete("/clients/9999")
    assert res.status_code == 404


# ── Workouts ──────────────────────────────────────────────────────────────────

def test_add_workout(client):
    client.post("/clients", json={"name": "Iris"})
    res = client.post("/workouts", json={
        "client_name": "Iris",
        "date": "2025-01-15",
        "workout_type": "Strength",
        "duration_min": 45
    })
    assert res.status_code == 201


def test_add_workout_missing_fields(client):
    res = client.post("/workouts", json={"client_name": "Nobody"})
    assert res.status_code == 400


def test_add_workout_no_body(client):
    res = client.post("/workouts", json={})
    assert res.status_code == 400


def test_get_workouts_by_client(client):
    client.post("/clients", json={"name": "Jake"})
    client.post("/workouts", json={"client_name": "Jake", "date": "2025-02-01", "workout_type": "Cardio"})
    res = client.get("/workouts?client=Jake")
    assert res.status_code == 200
    workouts = res.get_json()
    assert len(workouts) == 1
    assert workouts[0]["workout_type"] == "Cardio"


def test_get_all_workouts(client):
    res = client.get("/workouts")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_get_workouts_empty_client(client):
    res = client.get("/workouts?client=NoSuchPerson")
    assert res.status_code == 200
    assert res.get_json() == []


# ── Progress ──────────────────────────────────────────────────────────────────

def test_log_progress(client):
    client.post("/clients", json={"name": "Karen"})
    res = client.post("/progress", json={
        "client_name": "Karen",
        "week": "Week 1",
        "adherence": 85
    })
    assert res.status_code == 201


def test_log_progress_missing_adherence(client):
    res = client.post("/progress", json={"client_name": "Karen"})
    assert res.status_code == 400


def test_log_progress_missing_client(client):
    res = client.post("/progress", json={"adherence": 80})
    assert res.status_code == 400


def test_get_progress(client):
    client.post("/clients", json={"name": "Leo"})
    client.post("/progress", json={"client_name": "Leo", "week": "Week 1", "adherence": 90})
    client.post("/progress", json={"client_name": "Leo", "week": "Week 2", "adherence": 75})
    res = client.get("/progress/Leo")
    assert res.status_code == 200
    entries = res.get_json()
    assert len(entries) == 2
    assert entries[0]["adherence"] == 90


def test_get_progress_empty(client):
    res = client.get("/progress/NoSuchPerson")
    assert res.status_code == 200
    assert res.get_json() == []


# ── Program Generator ─────────────────────────────────────────────────────────

def test_generate_program_fat_loss(client):
    res = client.post("/generate-program", json={"goal": "fat_loss"})
    assert res.status_code == 200
    data = res.get_json()
    assert "program" in data
    assert data["goal"] == "fat_loss"


def test_generate_program_muscle_gain(client):
    res = client.post("/generate-program", json={"goal": "muscle_gain"})
    assert res.status_code == 200


def test_generate_program_beginner(client):
    res = client.post("/generate-program", json={"goal": "beginner"})
    assert res.status_code == 200


def test_generate_program_invalid_goal(client):
    res = client.post("/generate-program", json={"goal": "flying"})
    assert res.status_code == 400


def test_generate_program_updates_client(client):
    client.post("/clients", json={"name": "Mia"})
    client.post("/generate-program", json={"goal": "muscle_gain", "client_name": "Mia"})
    updated = client.get("/clients").get_json()[0]
    assert updated["program"] is not None


def test_generate_program_no_goal_defaults_beginner(client):
    res = client.post("/generate-program", json={})
    assert res.status_code == 200


# ── Membership ────────────────────────────────────────────────────────────────

def test_check_membership_active(client):
    client.post("/clients", json={"name": "Nick", "membership_status": "Active"})
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.get(f"/membership/{cid}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["membership_status"] == "Active"
    assert data["name"] == "Nick"


def test_check_membership_not_found(client):
    res = client.get("/membership/9999")
    assert res.status_code == 404