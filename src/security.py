import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_user_by_login

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACESS_TOKEN_EXPIRE_MINUTES", "30"))


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(username: str, password: str, db: AsyncSession):
    user = await get_user_by_login(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
