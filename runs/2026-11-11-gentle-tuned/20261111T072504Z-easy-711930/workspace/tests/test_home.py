from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_home():
    response = client.get('/')
    assert response.status_code == 200
    assert 'Come in. Sit down. Tell us about your human.' in response.text