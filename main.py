from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


ItemsList = {}


app = FastAPI()



@app.post("/items/")
async def create_item(item:Item):
    ItemsList[item.id] = item
    return ItemsList

@app.get("/items/")
async def read_items_list():
    return ItemsList

@app.get("/items/{item_id}")
async def read_items_detail(item_id: int):
    item = ItemsList.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item doesn't exist")
    return item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if ItemsList.get(item_id) is None:
        raise HTTPException(status_code=404, detail="Item doesn't exist")
    del ItemsList[item_id]
    return f"item {item_id} deleted successfully\nhere is Items list now:\n{ItemsList}"
