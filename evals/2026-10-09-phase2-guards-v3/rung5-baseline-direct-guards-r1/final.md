Files changed:
- export.py

Test output:
```
.FF.                                                                     [100%]
=================================== FAILURES ===================================
____________________ test_column_totals_ignores_text_cells _____________________

    def test_column_totals_ignores_text_cells():
>       assert column_totals([["a", 1], ["b", 2]]) == ["", 3]
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

test_export.py:11: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

rows = [['a', 1], ['b', 2]]

    def column_totals(rows):
        if not rows:
            return []
>       return [sum(r[i] for r in rows) for i in range(len(rows[0]))]
                ^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: unsupported operand type(s) for +: 'int' and 'str'

totals.py:4: TypeError
_____________________ test_render_marks_last_row_as_total ______________________

    def test_render_marks_last_row_as_total():
>       assert render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: render_rows() got an unexpected keyword argument 'mark_last'

test_export.py:15: TypeError
=========================== short test summary info ============================
FAILED test_export.py::test_column_totals_ignores_text_cells - TypeError: uns...
FAILED test_export.py::test_render_marks_last_row_as_total - TypeError: rende...
2 failed, 2 passed in 0.01s


Command exited with code 1
```

Anything not done: The other tests are still failing because column_totals doesn't handle text cells and render_rows doesn't support the mark_last parameter. These are separate issues not addressed by this change.