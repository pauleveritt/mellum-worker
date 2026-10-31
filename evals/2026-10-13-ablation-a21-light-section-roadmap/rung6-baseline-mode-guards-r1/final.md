Phase 1 implementation complete. Files changed:

1. `templates/base.html` - added favicon link
2. `app.py` - switched home route to use `home.html` template
3. `templates/home.html` - created home page template extending base layout with hero section
4. `tests/test_home.py` - added test for home page smoke test

Test output:
```
.                                                                        [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-pg_9vn2k/rung6/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-pg_9vn2k/rung6/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

tests/test_home.py::test_home_page
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-pg_9vn2k/rung6/.venv/lib/python3.14/site-packages/starlette/templating.py:161: DeprecationWarning: The `name` is not the first parameter anymore. The first parameter should be the `Request` instance.
  Replace `TemplateResponse(name, {"request": request})` by `TemplateResponse(request, name)`.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1 passed, 3 warnings in 0.38s
```

The test command exited with code 0, completing Phase 1.