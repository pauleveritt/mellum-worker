Implemented the `/sum` endpoint in `app.py` as specified in `specs/phase-7-sum.md`. The endpoint reads `numbers.txt` line by line and returns the sum of the two columns JSON-encoded.

```python
@app.get("/sum")
def sum_columns():
    col1_sum = 0
    col2_sum = 0
    with open("numbers.txt", "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                col1_sum += int(parts[0])
                col2_sum += int(parts[1])
    return {"col1": col1_sum, "col2": col2_sum}
```

The change has been verified; the route is now registered at line 78 of `app.py`. No modifications were made to `models.py`, `templates/`, or `tests/` as they are not required for this feature.