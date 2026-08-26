from pydantic import BaseModel
from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta, timezone
from config import Settings

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")


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


def get_password_hash(password):
    return password_hash.hash(password)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_user(db, username: str):
    if username in db:
        return UserInDB(**db[username])


def authenticate_user(fake_db, username: str, password: str):

    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


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


def create_access_token(data: dict, settings: Settings, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
