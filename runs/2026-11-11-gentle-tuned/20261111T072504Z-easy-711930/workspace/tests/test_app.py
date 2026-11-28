from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_home():
    response = client.get('/')
    assert response.status_code == 200
    assert 'Come in. Sit down. Tell us about your human.' in response.text

def test_board():
    response = client.get('/complaints')
    assert response.status_code == 200
    assert 'Scope creep never ends.' in response.text