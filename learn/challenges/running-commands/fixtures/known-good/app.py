from fastapi import FastAPI, HTTPException

app = FastAPI()
ITEMS = [{"id": 1, "name": "apple"}, {"id": 2, "name": "pear"}]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def items():
    return ITEMS


@app.get("/items/{item_id}")
def item(item_id: int):
    for found in ITEMS:
        if found["id"] == item_id:
            return found
    raise HTTPException(status_code=404, detail="not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
