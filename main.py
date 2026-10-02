from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from collections.abc import AsyncIterable, Iterable
from exceptions import ItemNotFoundError, DuplicateItemError
from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from jwt.exceptions import InvalidTokenError
from io import BytesIO
import httpx
import asyncio
import time
import jwt
import base64

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


# streaming responses and sse week5

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # برای تست؛ بعداً محدودش کن
    allow_methods=["*"],
    allow_headers=["*"],
)

test_string = "hello, this is a test response for stremingresponse learinng."

async def generate():

    yield "event: start\ndata: streaming started\n\n"

    for word in test_string.split():
        await asyncio.sleep(1)
        yield f"event: token\ndata: {word}\n\n"

    yield "event: end\ndata: done\n\n"


@app.get("/stream", tags=["Week5"])
async def stream():
    return StreamingResponse(generate(), media_type="text/event-stream")


# chaching week5

import random

random_sentences = [
    "random sentence for because any day.",
    "last one monday till post reset no black.",
    "reset your tune folks day north.",
]

cache: dict[str, str] = {}


class ChatRequest(BaseModel):
    prompt: str


@app.post("/chat-cache", tags=["Week5"])
async def cache_test(request: ChatRequest):
    key = request.prompt.strip().lower()

    if key in cache:
        return {"response": cache[key], "cached": True}

    await asyncio.sleep(2)

    response = random.choice(random_sentences)
    cache[key] = response

    return {"response": response, "cached": False}

# context management week5
random_sentences = [
    "random sentence for because any day.",
    "last one monday till post reset no black.",
    "reset your tune folks day north.",
]

system_prompt = {
    "role": "system",
    "content": "You are a helpful assistant.",
}

conversation: list[dict] = []

MAX_HISTORY = 6  # فقط آخرین ۶ پیام (user + assistant) نگه داشته می‌شود


class ChatRequest(BaseModel):
    prompt: str


@app.post("/chat", tags=["Week5"])
async def chat_with_history(request: ChatRequest):
    user_message = request.prompt.strip()

    conversation.append({"role": "user", "content": user_message})

    response = random.choice(random_sentences)

    conversation.append({"role": "assistant", "content": response})

    if len(conversation) > MAX_HISTORY:
        del conversation[: len(conversation) - MAX_HISTORY]

    history = [system_prompt] + conversation

    return {
        "response": response,
        "history": history,
    }


# Embeddings week6
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "I forgot my password.",
    "How can I reset my password?",
    "I cannot log into my account.",
    "I lost access to my account.",
    "The password reset link expired.",

    "The weather is sunny.",
    "It will rain tomorrow.",
    "Today's temperature is high.",

    "FastAPI is a Python framework.",
    "Django is a web framework.",
    "Python is a programming language.",
    ]


@app.get("/embedding", tags=["week6"])
async def embedding():

    embeddings = model.encode(sentences)
    scores = cosine_similarity([embeddings[0]], embeddings)

    return {"embeddings": embeddings.tolist(), "scores": scores.tolist()}

# week6 vector databases
from functools import lru_cache
from pinecone import Pinecone

settings = get_settings()

@lru_cache
def get_pinecone_index():
    pc = Pinecone(api_key=settings.pinecone_key)
    
    return pc.index("fastapi-tutorial")


vector_text = """
FastAPI is an async framework.
It works well with AI APIs.
Embeddings help semantic search.
"""
@app.get("/vector-upload", tags=["week6"])
async def upload_vector(text: str = vector_text):
    vector = model.encode(text).tolist()
    index = get_pinecone_index()

    print(len(vector))
    print("Pinecone key loaded:", bool(settings.pinecone_key))
    print("Pinecone key length:", len(settings.pinecone_key))


    index.upsert(
        vectors=[
        {
            "id": "doc1",
            "values": vector,
            "metadata": {
                "source": "manual.txt"
            }
        }
    ])

@app.post("/search", tags=["week6"])
async def search(question: str):
    query_vector = model.encode(question).tolist()

    index = get_pinecone_index()

    results = index.query(
        vector=query_vector,
        top_k=3,
        include_metadata=True
    )
    print(type(results))

    return results.to_dict()

# week 6 chunking

from langchain_text_splitters import RecursiveCharacterTextSplitter


chunk_text = """
# FastAPI Authentication Guide

FastAPI provides several ways to implement authentication and authorization in an API. 
One common approach is using JSON Web Tokens (JWT). In this approach, the user first 
sends their username and password to a login endpoint. After validating the credentials, 
the server creates an access token and returns it to the client.

## JWT Authentication

A JWT usually contains three parts: a header, a payload, and a signature. The payload 
can contain information such as the user's ID, username, or permissions. The server 
uses a secret key to sign the token, and the client sends the token with subsequent 
requests.
"""

@app.get("/fixed-chunking", tags=["week6"])
async def fixed_chunk(text: str = chunk_text, size: int = 100):
    return [text[i:i+size] for i in range(0, len(text), size)]


@app.get("/semantic-chunking", tags=["week6"])
async def semantic_chunk(text: str = chunk_text, size: int = 100):
    paragraph_chunks = text.split("\n\n")
    return paragraph_chunks


@app.get("/recursive-chunking", tags=["week6"])
async def recursive_chunk(text: str = chunk_text, size: int = 100, overlap: int = 20):
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)

    chunks = splitter.split_text(text)
    return chunks

# Week 7 - RAG Architecture

from openai import OpenAI

client = OpenAI(
    base_url=settings.openai_base_url,
    api_key=settings.openai_api_key,
)

rag_text = """
FastAPI is an async framework.
It works well with AI APIs.
Embeddings help semantic search.
"""


@app.post("/rag-upload", tags=["week7"])
async def rag_upload(text: str = rag_text):
    vector = model.encode(text).tolist()

    index = get_pinecone_index()

    index.upsert(
        vectors=[
            {
                "id": "rag_doc2",
                "values": vector,
                "metadata": {
                    "source": "rag_manual_2.txt",
                    "text": text,
                },
            }
        ]
    )

    return {"message": "Document uploaded successfully"}


@app.post("/rag-ask", tags=["week7"])
async def rag_ask(question: str):
    query_vector = model.encode(question).tolist()

    index = get_pinecone_index()

    results = index.query(
        vector=query_vector,
        top_k=3,
        include_metadata=True,
    )

    matches = results.to_dict()["matches"]

    context = [
        match["metadata"]["text"]
        for match in matches
        if "text" in match["metadata"] and match["score"] >= 0.5
    ]

    if not context:
        return {
            "question": question,
            "context": [],
            "sources": [],
            "answer": "I don't have enough information to answer this question.",
        }

    context_text = "\n\n".join(context)

    prompt = f"""
    You are a customer support assistant.

    Use the following context to answer the question.

    If the answer cannot be found in the context, say that you don't have enough information.

    Context:
    {context_text}

    Question:
    {question}
    """

    llm_response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a customer support assistant. "
                    "Answer only using the provided context. "
                    "If the answer is not supported by the context, "
                    "say that you don't have enough information."
                ),
            },
            {
                "role": "user",
                "content": f"""
        Context:
        {context_text}

        Question:
        {question}
        """,
            },
        ],
        extra_body={"reasoning": {"enabled": True}}
        )

    answer = llm_response.choices[0].message.content

    return {
        "question": question,
        "context": context,
        "sources": [
            {
                "id": match["id"],
                "score": match["score"],
                "source": match["metadata"].get("source"),
            }
            for match in matches
            if "text" in match["metadata"] and match["score"] >= 0.5
        ],
        "answer": answer,
    }