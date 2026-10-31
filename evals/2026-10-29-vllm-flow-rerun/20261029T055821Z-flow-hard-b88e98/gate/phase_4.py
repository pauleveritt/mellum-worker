from starlette.testclient import TestClient
from app import app

client = TestClient(app, follow_redirects=False)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text

def test_complaints_page():
    response = client.get("/complaints")
    assert response.status_code == 200
    assert "Scope creep never ends." in response.text

def test_post_complaints():
    response = client.post("/complaints", data={"agent_name": "TestAgent", "text": "Test complaint"})
    assert response.status_code == 303
    assert response.headers["Location"] == "/complaints"

def test_post_complaints_appears_on_page():
    # First post a complaint
    client.post("/complaints", data={"agent_name": "TestAgent2", "text": "Test complaint 2"})
    # GET /complaints
    response = client.get("/complaints")
    assert response.status_code == 200
    # Check that the new complaint appears in the response text
    assert "TestAgent2" in response.text
    assert "Test complaint 2" in response.text

def test_resolve_complaint():
    # Post a new complaint
    post_response = client.post("/complaints", data={"agent_name": "Resolver", "text": "To be resolved"})
    assert post_response.status_code == 303
    from models import complaints as model_complaints
    assert len(model_complaints) > 0
    complaint = model_complaints[-1]
    complaint_id = complaint.id
    # Resolve it
    resolve_response = client.post(f"/complaints/{complaint_id}/resolve", follow_redirects=False)
    assert resolve_response.status_code == 303
    assert resolve_response.headers["Location"] == "/complaints"
    # Get complaints page
    response = client.get("/complaints")
    assert response.status_code == 200
    # The complaint should now show as resolved
    assert "Resolved" in response.text
    # Re-import complaints to check the list
    from models import complaints as model_complaints_after
    assert len(model_complaints_after) == len(model_complaints)  # no new complaint added
    # The last complaint should still be the same id
    assert model_complaints_after[-1].id == complaint_id

def test_reopen_complaint():
    # Post a new complaint
    client.post("/complaints", data={"agent_name": "Reopener", "text": "To be reopened"})
    from models import complaints as model_complaints
    complaint = model_complaints[-1]
    complaint_id = complaint.id
    # It should be open initially
    # Resolve it
    client.post(f"/complaints/{complaint_id}/resolve", follow_redirects=False)
    # Now reopen it
    reopen_response = client.post(f"/complaints/{complaint_id}/reopen", follow_redirects=False)
    assert reopen_response.status_code == 303
    assert reopen_response.headers["Location"] == "/complaints"
    # Get complaints page
    response = client.get("/complaints")
    assert response.status_code == 200
    # The complaint should now be open again
    assert "Open" in response.text
    # Verify via model
    from models import complaints as model_complaints_after
    assert model_complaints_after[-1].id == complaint_id
    assert model_complaints_after[-1].status == "open"
