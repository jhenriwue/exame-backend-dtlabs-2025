import pytest
from fastapi.testclient import TestClient
from dtlabs.app import app

client = TestClient(app)

def test_get_sensor_data():
    response = client.get("/data")
    assert response.status_code == 401

def test_get_sensor_data_authenticated():
    client.post("/auth/register", json={"username": "user1", "password": "test123"})
    response1 = client.post("/auth/login", data={"username": "user1", "password": "test123"})
    tok = response1.json()["access_token"]
    token = f"Bearer {tok}"
    headers = {"Authorization": token}

    server = client.post("/servers", json={"server_name":"test433"})

    server_id = server.json()["server_ulid"]

    client.post("/data", json={"server_ulid":server_id,"timestamp":"2024-02-19T12:34:56Z", "temperature": 25.5, "humidity": 60.2,"voltage": 220.0,"current": 1.5},headers=headers)

    params = {
            "server_ulid": server_id,
            "start_time": "2024-03-01 00:00:00",
            "end_time": "2024-03-02 00:00:00",
            "sensor_type": "temperature",
            "aggregation": "minute"
        }
    
    response = client.get("/data", params=params,headers=headers)
    assert response.status_code == 200
