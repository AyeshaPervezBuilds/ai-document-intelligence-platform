"""Tests for document endpoints."""
import uuid


def _register_and_login(client):
    """Helper: register a new user and return their auth token."""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPass123!"
    client.post("/auth/register", json={"email": email, "password": password})
    login = client.post("/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def test_list_documents_empty(client):
    token = _register_and_login(client)
    response = client.get(
        "/documents", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_upload_document(client):
    token = _register_and_login(client)
    
    # Create a small dummy text file in memory
    files = {
        "file": ("test.txt", b"This is a test document about cloud computing.", "text/plain")
    }
    
    response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["status"] == "uploaded"
    assert "id" in data


def test_upload_unsupported_file_type(client):
    token = _register_and_login(client)
    files = {
        "file": ("test.exe", b"fake binary", "application/x-msdownload")
    }
    response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    # FastAPI will return 415 Unsupported Media Type
    assert response.status_code == 415


def test_upload_without_auth_fails(client):
    files = {"file": ("test.txt", b"hello", "text/plain")}
    response = client.post("/documents/upload", files=files)
    assert response.status_code in (401, 403)


def test_get_document_not_found(client):
    token = _register_and_login(client)
    fake_id = uuid.uuid4()
    response = client.get(
        f"/documents/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404  