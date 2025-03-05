import pytest
from fastapi.testclient import TestClient
from dtlabs.app import app

client = TestClient(app)

def test_register_user():
    response = client.post("/auth/register", json={"username": "user342", "password": "test123"})
    assert response.status_code == 200

def test_register_exist_user():
    client.post("/auth/register", json={"username": "user1", "password": "test123"})
    response = client.post("/auth/register", json={"username": "user1", "password": "test123"})
    assert response.status_code == 400

def test_login_user():
    client.post("/auth/register", json={"username": "user1", "password": "test123"})
    response = client.post("/auth/login", data={"username": "user1", "password": "test123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_user_not_exist():
    response = client.post("/auth/login", data={"username": "user2", "password": "test123"})
    assert response.status_code == 400
