The implementation of specs/phase-2-board.md is complete. Tests pass with 2 assertions successful.

**Files changed:**
- models.py: Added Complaint class and complaint list
- app.py: Imported complaints, added /complaints endpoint, fixed imports
- templates/complaints.html: Added template to display complaints board
- tests/test_app.py: Added test for complaints page

**Test output:**
```
..                                                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-6lmily4i/rung7/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

models.py:7
models.py:7
models.py:7
models.py:7
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-6lmily4i/rung7/models.py:7: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    self.created_at = datetime.utcnow()

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-6lmily4i/rung7/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2 passed, 7 warnings in 0.53s
```