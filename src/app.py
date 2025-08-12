from contextlib import asynccontextmanager
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from contracts import TimeSeries, Token, UserRegistration, UserResponse
from db import create_user, get_db, get_user_by_login, init_db
from security import (
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_access_token,
    get_password_hash,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user_by_login(db, username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserRegistration, db: Annotated[AsyncSession, Depends(get_db)]
):
    existing_user = await get_user_by_login(db, user_data.login)
    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this login already exists."
        )

    hashed_password = get_password_hash(user_data.password)
    db_user = await create_user(
        db=db,
        login=user_data.login,
        hashed_password=hashed_password,
        name=user_data.name,
        balance=0.0,
    )

    return UserResponse(
        id=db_user.id,
        login=db_user.login,
        name=db_user.name,
        balance=db_user.balance,
        time_series=[],
    )


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.login})
    return Token(access_token=access_token, token_type="bearer")


@app.get("/get_current_user_by_access_token", response_model=UserResponse)
async def get_current_user_by_access_token(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    return current_user
