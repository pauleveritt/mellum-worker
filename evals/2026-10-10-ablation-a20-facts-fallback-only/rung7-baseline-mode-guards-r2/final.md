Implemented specs/phase-2-board.md.

Changes made:
- Created `models.py` with `Complaint` class and seeded `complaints` list including "Scope creep never ends."
- Created `templates/complaints.html` to render the complaints board with agent name, text, and formatted date.
- Edited `app.py` to import `complaints` and add a `/complaints` route that renders `complaints.html`.
- Edited `tests/test_app.py` to add a test `test_complaints_board` that verifies `GET /complaints` returns 200 and contains "Scope creep never ends."

Test output:
```
..                                                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-jcge23wy/rung7/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

models.py:7
models.py:7
models.py:7
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-jcge23wy/rung7/models.py:7: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    self.creation_timestamp = datetime.utcnow()

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-jcge23wy/rung7/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2 passed, 6 warnings in 0.48s
```