The test `tests/test_phase4.py` now passes. Here are the changes made:

**Files changed:**
1. **models.py** - Added `id` and `status` fields to `Complaint`, implemented global `next_id` counter, and fixed `__post_init__` order.
2. **app.py** - Added `/complaints/{id}/resolve` and `/complaints/{id}/reopen` endpoints to handle status changes.
3. **templates/complaints.html** - Added display of complaint status next to each complaint.

**Test output:**
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-8.3.4, pluggy-1.6.0
rootdir: /private/var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-f9jrd4do/rung9
configfile: pyproject.toml
plugins: anyio-4.15.0
collected 2 items

tests/test_phase4.py ..                                                  [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-f9jrd4do/rung9/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-f9jrd4do/rung9/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 6 warnings in 0.65s =========================
```

The task is complete.