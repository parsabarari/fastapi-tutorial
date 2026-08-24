from fastapi import Depends, FastAPI, HTTPException
import time

from sqlalchemy.orm import Session
import httpx
import asyncio

import crud
import schemas
from database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# simple crud endpoints week2

@app.post("/items/", response_model=schemas.ItemResponse, tags=["CRUD"])
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.get("/items/", response_model=list[schemas.ItemResponse], tags=["CRUD"])
def read_items(db: Session = Depends(get_db)):
    return crud.get_items(db)


@app.get("/items/{item_id}", response_model=schemas.ItemResponse, tags=["CRUD"])
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)

    if item is None:
        raise HTTPException(404, "Item doesn't exist")

    return item


@app.delete("/items/{item_id}", tags=["CRUD"])
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.delete_item(db, item_id)

    if item is None:
        raise HTTPException(404, "Item doesn't exist")

    return {"message": f"Item {item_id} deleted"}


@app.put("/items/{item_id}", response_model=schemas.ItemResponse, tags=["CRUD"])
def update_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    updated = crud.update_item(db, item_id, item)

    if updated is None:
        raise HTTPException(404, "Item doesn't exist")

    return updated


# async testing and understanding endpoints week3

@app.get("/sync/", tags=["async_test"])
def sync_test():
    start = time.perf_counter()

    with httpx.Client() as client:
        response1 =  client.get("https://httpbin.org/delay/1")
        response2 =  client.get("https://httpbin.org/delay/1")
        response3 =  client.get("https://httpbin.org/delay/1")

    elapsed = time.perf_counter() - start
    return {"elapsed_time": elapsed, "data": [response1.json(), response2.json(), response3.json()]}


@app.get("/async/", tags=["async_test"])
async def async_test_sequential():
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        response1 = await client.get("https://httpbin.org/delay/1")
        response2 = await client.get("https://httpbin.org/delay/1")
        response3 = await client.get("https://httpbin.org/delay/1")
    elapsed = time.perf_counter() - start
    return {"elapsed_time": elapsed, "data": [response1.json(), response2.json(), response3.json()]}


@app.get("/asyncc/", tags=["async_test"])
async def async_test_concurrent():
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(
            client.get("https://httpbin.org/delay/1"),
            client.get("https://httpbin.org/delay/1"),
            client.get("https://httpbin.org/delay/1")
        )
    elapsed = time.perf_counter() - start
    return {"elapsed_time": elapsed, "data": [response.json() for response in responses]}
