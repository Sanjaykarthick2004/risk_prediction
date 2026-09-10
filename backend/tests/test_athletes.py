def test_create_and_get_athlete(client, auth_headers):
    payload = {
        "athlete_id": "PYTEST-001", "name": "Pytest Athlete", "age": 22, "gender": "Male",
        "sport": "Running", "event_type": "Long Distance", "height": 180, "weight": 78, "experience_years": 4,
    }
    res = client.post("/api/athletes", json=payload, headers=auth_headers)
    assert res.status_code == 201

    get_res = client.get("/api/athletes/PYTEST-001", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Pytest Athlete"


def test_duplicate_athlete_rejected(client, auth_headers):
    payload = {
        "athlete_id": "PYTEST-002", "name": "Dup", "age": 22, "gender": "Male",
        "sport": "Running", "event_type": "Long Distance", "height": 180, "weight": 78, "experience_years": 4,
    }
    client.post("/api/athletes", json=payload, headers=auth_headers)
    res = client.post("/api/athletes", json=payload, headers=auth_headers)
    assert res.status_code == 409


def test_update_athlete(client, auth_headers):
    payload = {
        "athlete_id": "PYTEST-003", "name": "Update Me", "age": 22, "gender": "Male",
        "sport": "Running", "event_type": "Long Distance", "height": 180, "weight": 78, "experience_years": 4,
    }
    client.post("/api/athletes", json=payload, headers=auth_headers)
    res = client.put("/api/athletes/PYTEST-003", json={"age": 23}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["age"] == 23


def test_delete_athlete(client, auth_headers):
    payload = {
        "athlete_id": "PYTEST-004", "name": "Delete Me", "age": 22, "gender": "Male",
        "sport": "Running", "event_type": "Long Distance", "height": 180, "weight": 78, "experience_years": 4,
    }
    client.post("/api/athletes", json=payload, headers=auth_headers)
    res = client.delete("/api/athletes/PYTEST-004", headers=auth_headers)
    assert res.status_code == 204
    assert client.get("/api/athletes/PYTEST-004", headers=auth_headers).status_code == 404


def test_get_nonexistent_athlete_returns_404(client, auth_headers):
    res = client.get("/api/athletes/PYTEST-DOES-NOT-EXIST", headers=auth_headers)
    assert res.status_code == 404


def test_invalid_athlete_data_rejected(client, auth_headers):
    bad_payload = {
        "athlete_id": "PYTEST-BAD", "name": "Bad", "age": 200,  # out of range
        "gender": "Male", "sport": "Running", "event_type": "Long Distance",
        "height": 180, "weight": 78, "experience_years": 4,
    }
    res = client.post("/api/athletes", json=bad_payload, headers=auth_headers)
    assert res.status_code == 422


def test_athlete_id_is_auto_generated_when_omitted(client, auth_headers):
    payload = {
        "name": "Auto ID Athlete", "age": 22, "gender": "Male", "sport": "Running",
        "event_type": "Long Distance", "height": 180, "weight": 78, "experience_years": 4,
    }
    res = client.post("/api/athletes", json=payload, headers=auth_headers)
    assert res.status_code == 201
    body = res.json()
    assert body["athlete_id"]
    assert body["athlete_id"].startswith("ATH-")

    # A second athlete created the same way gets a different, incrementing id.
    res2 = client.post("/api/athletes", json=payload, headers=auth_headers)
    assert res2.json()["athlete_id"] != body["athlete_id"]
