from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from exceptions import ItemNotFoundError, DuplicateItemError
from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from jwt.exceptions import InvalidTokenError
import httpx
import asyncio
import time
import jwt

import crud
import schemas
from database import Base, SessionLocal, engine
from config import Settings, get_settings
from auth_models import create_access_token

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.exception_handler(ItemNotFoundError)
def item_not_found_handler(request, exc: ItemNotFoundError):
    return JSONResponse(status_code=404, content={"detail": f"Item {exc.item_id} not found"})


@app.exception_handler(DuplicateItemError)
def duplicate_item_handler(request, exc: DuplicateItemError):
    return JSONResponse(status_code=409, content={"detail": f"Item {exc.item_id} already exists"})


# simple crud endpoints week2

@app.post("/items/", response_model=schemas.ItemResponse, tags=["CRUD"])
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.get("/items/", response_model=list[schemas.ItemResponse], tags=["CRUD"])
def read_items(db: Session = Depends(get_db)):
    return crud.get_items(db)


@app.get("/items/{item_id}", response_model=schemas.ItemResponse, tags=["CRUD"])
def read_item(item_id: int, db: Session = Depends(get_db)):
    return crud.get_item(db, item_id)


@app.delete("/items/{item_id}", tags=["CRUD"])
def delete_item(item_id: int, db: Session = Depends(get_db)):
    crud.delete_item(db, item_id)
    return {"message": f"Item {item_id} deleted"}


@app.put("/items/{item_id}", response_model=schemas.ItemResponse, tags=["CRUD"])
def update_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    return crud.update_item(db, item_id, item)


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


# authentication & authorization week3



# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30



class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    role: str


class UserInDB(User):
    hashed_password: str


password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin123"),
        "disabled": False,
        "role": "admin",
    },
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": get_password_hash("secret"),
        "disabled": False,
        "role": "user",
    },
}


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


@app.post("/token", tags=["auth"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    from fastapi import HTTPException, status

    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
        settings=settings,
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", tags=["auth"])
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user


@app.get("/users/me/items/", tags=["auth"])
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.get("/admin/users", tags=["auth"])
async def list_users(current_user: Annotated[User, Depends(get_current_admin)]):
    return [{"username": u["username"], "role": u["role"]} for u in fake_users_db.values()]
