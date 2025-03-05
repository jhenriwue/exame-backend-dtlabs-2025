import pytest
from fastapi.testclient import TestClient
from dtlabs.app import app

client = TestClient(app)

def test_list_servers():
    response = client.get("/health/all/")
    assert response.status_code == 401

def test_list_servers_auth():
    client.post("/auth/register", json={"username": "user1", "password": "test123"})
    
    response = client.post("/auth/login", data={"username": "user1", "password": "test123"})
    print("Login Response:", response.json())  # <-- Adicionado para depuração

    assert response.status_code == 200  # Garante que o login foi bem-sucedido

    tok = response.json().get("access_token")  # Pode retornar None se o login falhou

    assert tok is not None, "Token de autenticação não foi gerado!"

    token = f"Bearer {tok}"
    headers = {"Authorization": token}
    
    response = client.get("/health/all/", headers=headers)
    print("Health Response:", response.json())  # <-- Adicionado para depuração

    assert response.status_code == 200  # O esperado é que retorne sucesso
