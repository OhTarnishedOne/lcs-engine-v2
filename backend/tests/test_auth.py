def test_register(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass456"},
    )
    assert response.status_code == 409


def test_login(client):
    # Register first
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    # Then login
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_me(client):
    # Register and get token
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = reg_response.json()["access_token"]

    # Access /me
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_me_no_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_refresh_token(client):
    # Register and get refresh token
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    refresh_token = reg_response.json()["refresh_token"]

    # Use refresh token
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
