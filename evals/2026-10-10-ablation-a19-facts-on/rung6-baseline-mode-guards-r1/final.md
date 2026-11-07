Implementation complete. The specifications for phase 1 home page have been implemented:

- `app.py` now imports `Request`, types the home function accordingly, and includes the `if __name__ == "__main__":` block to run uvicorn with reload.
- `templates/base.html` contains the HTML5 layout with Bootstrap 5 CDN, favicon, and navbar as specified.
- `templates/home.html` extends base layout and provides the hero section with the required tagline.
- `models.py` exists (minimal placeholder).
- `tests/test_home.py` verifies the home page returns 200 and contains the tagline.
- Running `uv run python -m pytest tests` now passes.

The task is done.