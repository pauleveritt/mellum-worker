from starlette.testclient import TestClient
from app import app

client = TestClient(app, follow_redirects=False)

def test_home_page_returns_200_and_tagline():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text

def test_home_page_layout_contains_expected_elements():
    response = client.get("/")
    # Favicon
    assert 'href="https://www.python.org/static/favicon.ico"' in response.text
    # Navbar links
    assert 'href="/complaints"' in response.text
    assert 'href="/"' in response.text
    # Title
    assert "AgentClinic" in response.text
    # Responsive viewport meta tag
    assert 'meta name="viewport"' in response.text or 'viewport' in response.text

def test_app_uvicorn_run_reload_flag():
    import os
    import inspect
    try:
        from app import app as fastapi_app
        app_path = inspect.getfile(fastapi_app)
    except ImportError:
        app_path = "app.py"
    if not os.path.exists(app_path):
        assert False, f"app.py not found at {app_path}"
    with open(app_path, "r") as f:
        source = f.read()
    lines = source.splitlines()
    in_main_block = False
    run_with_reload_found = False
    for line in lines:
        if "__main__" in line and "if __name__ == \"__main__\"" in line:
            in_main_block = True
        if in_main_block and "uvicorn.run" in line and "reload=True" in line:
            run_with_reload_found = True
            break
    assert in_main_block, "No __name__ == '__main__' block found"
    assert run_with_reload_found, "uvicorn.run with reload=True not found inside __name__ == '__main__' block"
