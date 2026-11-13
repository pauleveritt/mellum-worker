The `/sum` endpoint has been added to `app.py` as specified in `specs/phase-7-sum.md`. It streams `numbers.txt` line by line and returns the summed columns:

```json
{"col1": <sum>, "col2": <sum>}
```

You can now run the application and query `GET /sum` to retrieve the totals.