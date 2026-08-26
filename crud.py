from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas
from exceptions import ItemNotFoundError, DuplicateItemError


def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateItemError(item.id)
    db.refresh(db_item)
    return db_item


def get_items(db: Session):
    return db.query(models.Item).all()


def get_item(db: Session, item_id: int):
    item = db.get(models.Item, item_id)
    if item is None:
        raise ItemNotFoundError(item_id)
    return item


def delete_item(db: Session, item_id: int):
    item = db.get(models.Item, item_id)
    if item is None:
        raise ItemNotFoundError(item_id)
    db.delete(item)
    db.commit()
    return item


def update_item(db: Session, item_id: int, data: schemas.ItemUpdate):
    item = db.get(models.Item, item_id)
    if item is None:
        raise ItemNotFoundError(item_id)

    for key, value in data.model_dump().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item
