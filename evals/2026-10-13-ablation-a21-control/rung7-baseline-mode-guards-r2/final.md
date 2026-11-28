Files changed:
- models.py
- app.py
- templates/complaints.html
- tests/test_complaints.py

Test output:
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-8.3.4, pluggy-1.6.0
rootdir: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ucbxk_ed/rung7
configfile: pyproject.toml
plugins: anyio-4.15.0
collected 2 items

tests/test_app.py .                                                      [ 50%]
tests/test_complaints.py .                                               [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ucbxk_ed/rung7/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

models.py:8
models.py:8
models.py:8
models.py:8
models.py:8
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ucbxk_ed/rung7/models.py:8: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    self.created_at = datetime.utcnow()

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ucbxk_ed/rung7/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 8 warnings in 0.39s =========================
```