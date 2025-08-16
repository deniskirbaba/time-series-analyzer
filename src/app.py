from contextlib import asynccontextmanager
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from contracts import (
    TimeSeriesCreate,
    TimeSeriesResponse,
    Token,
    UserRegistration,
    UserResponse,
)
from db import (
    create_time_series,
    create_user,
    delete_time_series,
    get_db,
    get_time_series_by_id,
    get_user_by_login,
    init_db,
    update_user_balance,
)
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
) -> UserResponse:
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

    return UserResponse(
        id=user.id,
        login=user.login,
        name=user.name,
        balance=user.balance,
        time_series=[ts.id for ts in user.time_series],
    )


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


@app.post("/top_up_balance", response_model=UserResponse)
async def top_up_balance(
    amount: float,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    updated_user = await update_user_balance(db, current_user.id, amount)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=updated_user.id,
        login=updated_user.login,
        name=updated_user.name,
        balance=updated_user.balance,
        time_series=[ts.id for ts in updated_user.time_series],
    )


@app.post("/time_series", response_model=TimeSeriesResponse)
async def create_time_series_endpoint(
    ts_data: TimeSeriesCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not ts_data.data:
        raise HTTPException(status_code=400, detail="Data cannot be empty")

    db_ts = await create_time_series(
        db=db, user_id=ts_data.user_id, name=ts_data.name, data=ts_data.data
    )

    return TimeSeriesResponse(
        id=db_ts.id,
        user_id=db_ts.user_id,
        name=db_ts.name,
        created_at=db_ts.created_at,
        length=db_ts.length,
        data=db_ts.data,
        analysis_results=db_ts.analysis_results,
        forecasting_ts=db_ts.forecasting_ts,
    )


@app.get("/time_series/{ts_id}", response_model=TimeSeriesResponse)
async def get_time_series_endpoint(
    ts_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    db_ts = await get_time_series_by_id(db, ts_id)

    if not db_ts:
        raise HTTPException(status_code=404, detail="Time series not found")

    return TimeSeriesResponse(
        id=db_ts.id,
        user_id=db_ts.user_id,
        name=db_ts.name,
        created_at=db_ts.created_at,
        length=db_ts.length,
        data=db_ts.data,
        analysis_results=db_ts.analysis_results,
        forecasting_ts=db_ts.forecasting_ts,
    )


@app.delete("/time_series/{ts_id}")
async def delete_time_series_endpoint(
    ts_id: int,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    success = await delete_time_series(db, ts_id, user_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Time series not found or you don't have permission to delete it",
        )

    return {"message": "Time series deleted successfully"}
