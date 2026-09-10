def test_register_and_login(client):
    res = client.post("/api/auth/register", json={"username": "pytest_user1", "password": "testpass123", "role": "RESEARCHER"})
    assert res.status_code == 201
    assert "password" not in res.text  # never expose plaintext or the hash

    login_res = client.post("/api/auth/login", data={"username": "pytest_user1", "password": "testpass123"})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_login_rejects_wrong_password(client):
    client.post("/api/auth/register", json={"username": "pytest_user2", "password": "correctpass", "role": "RESEARCHER"})
    res = client.post("/api/auth/login", data={"username": "pytest_user2", "password": "wrongpass"})
    assert res.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {"username": "pytest_dup", "password": "testpass123", "role": "RESEARCHER"}
    client.post("/api/auth/register", json=payload)
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 409


def test_me_requires_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_with_valid_token(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["username"] == "pytest_researcher"


def test_forgot_and_reset_password_flow(client):
    client.post("/api/auth/register", json={"username": "pytest_forgot", "password": "oldpassword", "role": "RESEARCHER"})

    forgot_res = client.post("/api/auth/forgot-password", json={"username": "pytest_forgot"})
    assert forgot_res.status_code == 200
    dev_link = forgot_res.json()["dev_link"]
    assert dev_link
    token = dev_link.split("token=")[1]

    reset_res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "newpassword123"})
    assert reset_res.status_code == 200

    old_login = client.post("/api/auth/login", data={"username": "pytest_forgot", "password": "oldpassword"})
    assert old_login.status_code == 401

    new_login = client.post("/api/auth/login", data={"username": "pytest_forgot", "password": "newpassword123"})
    assert new_login.status_code == 200

    # token is single-use
    reuse_res = client.post("/api/auth/reset-password", json={"token": token, "new_password": "another123"})
    assert reuse_res.status_code == 400


def test_forgot_password_unknown_username_does_not_leak_existence(client):
    res = client.post("/api/auth/forgot-password", json={"username": "pytest_no_such_user"})
    assert res.status_code == 200
    assert res.json()["dev_link"] is None


def test_reset_password_invalid_token_rejected(client):
    res = client.post("/api/auth/reset-password", json={"token": "not-a-real-token", "new_password": "whatever123"})
    assert res.status_code == 400
