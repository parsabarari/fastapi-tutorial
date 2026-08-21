from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class ItemCreate(ItemBase):
    id: int


class ItemUpdate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
