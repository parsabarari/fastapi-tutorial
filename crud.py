from sqlalchemy.orm import Session

import models
import schemas


def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_items(db: Session):
    return db.query(models.Item).all()


def get_item(db: Session, item_id: int):
    return db.get(models.Item, item_id)


def delete_item(db: Session, item_id: int):
    item = db.get(models.Item, item_id)

    if item is None:
        return None

    db.delete(item)
    db.commit()
    return item


def update_item(db: Session, item_id: int, data: schemas.ItemUpdate):
    item = db.get(models.Item, item_id)

    if item is None:
        return None

    values = data.model_dump()

    for key, value in values.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    return item
