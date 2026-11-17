The export now includes a totals row when requested. The necessary changes were made to `export.py`, `totals.py`, and `render.py` to handle totals calculation and rendering. All tests pass:

```
....                                                                     [100%]
4 passed in 0.01s
```

Files modified:
- export.py: Added totals parameter and logic to append total row
- totals.py: Fixed column_totals to safely handle mixed data types
- render.py: Added mark_last parameter support for legacy compatibility

The issue is resolved.