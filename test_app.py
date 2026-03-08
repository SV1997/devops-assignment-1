"""
test_app.py — Pytest suite for ACEest Fitness & Gym Flask API
"""
import os
import pytest

# Use in-memory SQLite so tests never touch a real file
os.environ["DB_NAME"] = ":memory:"

from app import app, init_db   # noqa: E402


@pytest.fixture
def client():
    """Create a fresh test client with an initialized DB before each test."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        with app.app_context():
            init_db()
        yield c



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



def _add_client(client, name="Alice", **kwargs):
    payload = {"name": name, **kwargs}
    return client.post("/clients", json=payload)


def test_add_client(client):
    res = _add_client(client, name="Alice", age=28, weight=65.0)
    assert res.status_code == 201
    assert "Alice" in res.get_json()["message"]


def test_add_client_missing_name(client):
    res = client.post("/clients", json={"age": 30})
    assert res.status_code == 400


def test_add_duplicate_client(client):
    _add_client(client, name="Bob")
    res = _add_client(client, name="Bob")
    assert res.status_code == 409


def test_get_clients_empty(client):
    res = client.get("/clients")
    assert res.status_code == 200
    assert res.get_json() == []


def test_get_clients(client):
    _add_client(client, name="Carol")
    res = client.get("/clients")
    assert res.status_code == 200
    names = [c["name"] for c in res.get_json()]
    assert "Carol" in names


def test_get_client_by_id(client):
    _add_client(client, name="Dave", age=35)
    all_clients = client.get("/clients").get_json()
    cid = all_clients[0]["id"]
    res = client.get(f"/clients/{cid}")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Dave"


def test_get_client_not_found(client):
    res = client.get("/clients/9999")
    assert res.status_code == 404


def test_update_client(client):
    _add_client(client, name="Eve")
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
    _add_client(client, name="Frank")
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.put(f"/clients/{cid}", json={"nonexistent_field": "xyz"})
    assert res.status_code == 400


def test_delete_client(client):
    _add_client(client, name="Grace")
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.delete(f"/clients/{cid}")
    assert res.status_code == 200
    assert client.get(f"/clients/{cid}").status_code == 404


def test_delete_client_not_found(client):
    res = client.delete("/clients/9999")
    assert res.status_code == 404



def test_add_workout(client):
    _add_client(client, name="Hank")
    res = client.post("/workouts", json={
        "client_name": "Hank",
        "date": "2025-01-15",
        "workout_type": "Strength",
        "duration_min": 45
    })
    assert res.status_code == 201


def test_add_workout_missing_fields(client):
    res = client.post("/workouts", json={"client_name": "Nobody"})
    assert res.status_code == 400


def test_get_workouts(client):
    _add_client(client, name="Iris")
    client.post("/workouts", json={"client_name": "Iris", "date": "2025-02-01", "workout_type": "Cardio"})
    res = client.get("/workouts?client=Iris")
    assert res.status_code == 200
    workouts = res.get_json()
    assert len(workouts) == 1
    assert workouts[0]["workout_type"] == "Cardio"


def test_get_all_workouts(client):
    res = client.get("/workouts")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)



def test_log_progress(client):
    _add_client(client, name="Jake")
    res = client.post("/progress", json={"client_name": "Jake", "week": "Week 1", "adherence": 85})
    assert res.status_code == 201


def test_log_progress_missing_fields(client):
    res = client.post("/progress", json={"client_name": "Jake"})
    assert res.status_code == 400


def test_get_progress(client):
    _add_client(client, name="Karen")
    client.post("/progress", json={"client_name": "Karen", "week": "Week 1", "adherence": 90})
    client.post("/progress", json={"client_name": "Karen", "week": "Week 2", "adherence": 75})
    res = client.get("/progress/Karen")
    assert res.status_code == 200
    entries = res.get_json()
    assert len(entries) == 2
    assert entries[0]["adherence"] == 90


def test_get_progress_empty(client):
    res = client.get("/progress/NoSuchPerson")
    assert res.status_code == 200
    assert res.get_json() == []



def test_generate_program_valid_goal(client):
    res = client.post("/generate-program", json={"goal": "fat_loss"})
    assert res.status_code == 200
    data = res.get_json()
    assert "program" in data
    assert data["goal"] == "fat_loss"


def test_generate_program_invalid_goal(client):
    res = client.post("/generate-program", json={"goal": "flying"})
    assert res.status_code == 400


def test_generate_program_updates_client(client):
    _add_client(client, name="Leo")
    res = client.post("/generate-program", json={"goal": "muscle_gain", "client_name": "Leo"})
    assert res.status_code == 200
    updated = client.get("/clients").get_json()[0]
    assert updated["program"] is not None


def test_generate_program_no_body(client):
    res = client.post("/generate-program", json={})
    # Defaults to 'beginner' → valid
    assert res.status_code == 200



def test_check_membership(client):
    _add_client(client, name="Mia", membership_status="Active")
    cid = client.get("/clients").get_json()[0]["id"]
    res = client.get(f"/membership/{cid}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["membership_status"] == "Active"
    assert data["name"] == "Mia"


def test_check_membership_not_found(client):
    res = client.get("/membership/9999")
    assert res.status_code == 404