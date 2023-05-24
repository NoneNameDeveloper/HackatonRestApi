# ТЕСТЫ

from fastapi.testclient import TestClient

from .conversation import app

client = TestClient(app)


def test_text_prompt():
    response = client.get("/text_prompt", params={
        "user_id": 2,
        "text": "Hello!",
        "token": "0XSno3QRE6dOEpM6EH7F0A"
    })
    assert response.status_code == 200
    assert response.json()['status'] == "SUCCESS"
    assert response.json()['id_'] != ""
    assert response.json()['result'] != ""


def test_text_wrong_token():
    response = client.get("/text_prompt", params={
        "user_id": 2,
        "text": "Hello!",
        "token": "wrong"
    })

    assert response.status_code == 403
    assert response.json() == {"status": "INVALID_API_TOKEN"}


def test_reset_state():
    response = client.get("/reset_state", params={
        "user_id": 2,
        "token": "0XSno3QRE6dOEpM6EH7F0A"
    })

    assert response.status_code == 200
    assert response.json() in [{"status": "SUCCESS"}, {"status": "NOTHING_TO_RESET"}]


def test_reset_state_wrong_token():
    response = client.get("/reset_state", params={
        "user_id": 2,
        "token": "wrong"
    })

    assert response.status_code == 403
    assert response.json() == {"status": "INVALID_API_TOKEN"}


def test_rate_chat():
    response = client.get("/rate_chat", params={
        "user_id": 2,
        "token": "0XSno3QRE6dOEpM6EH7F0A",
        "rate": 5
    })

    assert response.status_code == 200
    assert response.json() in [{"status": "NOTHING_TO_RATE"}, {"status": "SUCCESS"}]


def test_rate_chat_wrong_token():
    response = client.get("/rate_chat", params={
        "user_id": 2,
        "token": "wrong",
        "rate": 5
    })

    assert response.status_code == 403
    assert response.json() == {"status": "INVALID_API_TOKEN"}