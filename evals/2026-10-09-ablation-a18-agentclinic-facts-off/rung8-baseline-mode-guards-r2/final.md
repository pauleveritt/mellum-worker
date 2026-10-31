The task implementing specs/phase-3-add.md is complete. Changes made:

1. **app.py**: Added POST /complaints route, RedirectResponse import, and uvicorn runner logic. Updated imports to use FastAPI responses.
2. **models.py**: No changes needed (already had Complaint class and sample data).
3. **templates/complaints.html**: Added complaint submission form at the end of the page.
4. **pyproject.toml**: Added uvicorn dependency.
5. **pytest.ini**: Added to set Python path for tests.
6. **__init__.py**: Added empty file to support Python package structure.

Test output:
```
..                                                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-crrgzw6g/rung8/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-crrgzw6g/rung8/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2 passed, 4 warnings in 0.61s
```

The test command `uv run --offline pytest -q` now exits 0, completing the task.