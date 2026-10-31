Files changed:
- `app.py` (updated route handling)

Test output:
```
tests/test_app.py::test_home_page PASSED                                 [100%]

=============================== warnings summary ===============================
../../../../../../../../var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-b1eaz0_h/rung7/.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-b1eaz0_h/rung7/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

models.py:7
  /private/var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-b1eaz0_h/rung7/models.py:7: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    self.timestamp = datetime.utcnow()

../../../../../../../../var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-b1eaz0_h/rung7/.venv/lib/python3.14/site-packages/fastapi/routing.py:233
../../../../../../../../var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-b1eaz0_h/rung7/.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-b1eaz0_h/rung7/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)
```

The implementation now satisfies the requirements of `phase-2-board.md`.