def test_register(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "seeker@example.com",
            "password": "secret123",
            "full_name": "Test Seeker",
            "role": "seeker",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "User registered successfully."
    assert "access_token" in data
    assert data["user"]["email"] == "seeker@example.com"
    assert data["user"]["role"] == "seeker"


def test_login(client):
    client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "secret123",
            "full_name": "Login User",
            "role": "seeker",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


def test_forgot_and_reset_password(client):
    client.post(
        "/api/auth/register",
        json={
            "email": "reset@example.com",
            "password": "secret123",
            "full_name": "Reset User",
            "role": "seeker",
        },
    )

    forgot = client.post(
        "/api/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    assert forgot.status_code == 200
    token = forgot.get_json()["reset_token"]

    reset = client.post(
        "/api/auth/reset-password",
        json={
            "email": "reset@example.com",
            "token": token,
            "password": "newsecret123",
        },
    )
    assert reset.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "newsecret123"},
    )
    assert login.status_code == 200
