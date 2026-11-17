from starlette.testclient import TestClient
from app import app

client = TestClient(app, follow_redirects=False)

def test_home_page_returns_200_and_tagline():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text

def test_app_py_calls_uvicorn_run_with_reload_true_inside_main_block():
    import os
    from pathlib import Path
    app_py_path = Path(__file__).resolve().parent.parent / "app.py"
    assert app_py_path.exists(), f"app.py not found at {app_py_path}"
    content = app_py_path.read_text()
    assert "uvicorn.run" in content, "uvicorn.run not found in app.py"
    assert "reload=True" in content, "reload=True not found in app.py"
    lines = content.splitlines()
    main_block_found = False
    run_found = False
    for line in lines:
        if "__name__ == \"__main__\"" in line:
            main_block_found = True
        if "uvicorn.run" in line and "reload=True" in line:
            run_found = True
    assert main_block_found, "__name__ == \"__main__\" block not found in app.py"
    assert run_found, "uvicorn.run with reload=True not found in app.py"
