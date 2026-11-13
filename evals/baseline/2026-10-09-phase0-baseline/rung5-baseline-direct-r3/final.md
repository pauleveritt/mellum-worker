Files changed:
- export.py
- totals.py

Test output:
```
..F.                                                                     [100%]
=================================== FAILURES ===================================
_____________________ test_render_marks_last_row_as_total ______________________

    def test_render_marks_last_row_as_total():
>       assert render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: render_rows() got an unexpected keyword argument 'mark_last'

test_export.py:15: TypeError
=========================== short test summary info ============================
FAILED test_export.py::test_render_marks_last_row_as_total - TypeError: rende...
1 failed, 3 passed in 0.01s
```

 anything not done: The test `test_render_marks_last_row_as_total` is still failing because `render_rows` does not support the `mark_last` parameter. This may require additional changes to `render.py` or the test.