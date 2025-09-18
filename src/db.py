import json
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import attributes, selectinload
from sqlalchemy.pool import StaticPool

from data_models import Base, Forecast, Model, Task, TimeSeries, User

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, expire_on_commit=False
)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


async def get_user_by_login(db: AsyncSession, login: str) -> User | None:
    result = await db.execute(select(User).filter(User.login == login))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, id: int) -> User | None:
    result = await db.execute(select(User).filter(User.id == id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, login: str, hashed_password: str, name: str, balance: float = 0.0
) -> User:
    db_user = User(
        login=login, hashed_password=hashed_password, name=name, balance=balance
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user_balance(
    db: AsyncSession, user_id: int, amount: float
) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user:
        user.balance += amount
        await db.commit()
        await db.refresh(user)
    return user


async def withdraw_user_balance(
    db: AsyncSession, user_id: int, amount: float
) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user:
        if user.balance < amount:
            return None
        user.balance -= amount
        await db.commit()
        await db.refresh(user)
    return user


async def create_time_series(
    db: AsyncSession, user_id: int, name: str, data: list[float]
) -> TimeSeries:

    db_ts = TimeSeries(
        user_id=user_id,
        name=name,
        created_at=datetime.now().isoformat(),
        length=len(data),
        data=data,
        analysis_results={},
        forecasting_ts=[],
    )
    db.add(db_ts)
    await db.commit()
    await db.refresh(db_ts)
    return db_ts


async def get_time_series_by_id(db: AsyncSession, ts_id: int):
    result = await db.execute(select(TimeSeries).where(TimeSeries.id == ts_id))
    return result.scalars().first()


async def delete_time_series(db: AsyncSession, ts_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(TimeSeries).filter(TimeSeries.id == ts_id, TimeSeries.user_id == user_id)
    )
    ts = result.scalar_one_or_none()
    if ts:
        await db.delete(ts)
        await db.commit()
        return True
    return False


async def add_forecast_ts_id(db: AsyncSession, ts_id: int, forecast_ts_id: int):
    ts = await get_time_series_by_id(db, ts_id)

    ts_for_ts = ts.forecasting_ts or []
    ts_for_ts.append(forecast_ts_id)

    ts.forecasting_ts = ts_for_ts[:]  # Create a new list copy
    attributes.flag_modified(ts, "forecasting_ts")

    await db.commit()
    await db.refresh(ts)


async def populate_models(db: AsyncSession, json_path: str | Path):
    with open(json_path, "r") as f:
        data = json.load(f)

    result = await db.execute(select(Model))
    existing_models = result.scalars().all()
    for model in existing_models:
        await db.delete(model)

    models = [Model(**model_data) for model_data in data.values()]
    db.add_all(models)
    await db.commit()


async def get_all_models(db: AsyncSession) -> list[Model]:
    result = await db.execute(select(Model))
    return result.scalars().all()


async def create_task(
    db: AsyncSession,
    ts_id: int,
    user_id: int,
    cost: float,
    type: str,
    params: str,
    status: str,
) -> Task:
    db_task = Task(
        ts_id=ts_id,
        user_id=user_id,
        cost=cost,
        type=type,
        params=params,
        status=status,
        updated_at=datetime.now().isoformat(),
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def get_tasks_for_user(db: AsyncSession, user_id: int) -> list[Task]:
    result = await db.execute(select(Task).filter(Task.user_id == user_id))
    return result.scalars().all()


async def get_task_by_task_id(db: AsyncSession, task_id: int) -> Task | None:
    result = await db.execute(select(Task).filter(Task.id == task_id))
    return result.scalar_one_or_none()


async def update_task_by_task_id(db: AsyncSession, task_id: int, status: str):
    task = await db.get(Task, task_id)
    if task:
        task.status = status
        task.updated_at = datetime.now().isoformat()
        await db.commit()


async def update_analysis_results(db: AsyncSession, ts_id: int, results: dict):
    ts = await db.get(TimeSeries, ts_id)
    if ts:
        ts.analysis_results = results
        await db.commit()


async def create_forecast(
    db: AsyncSession, model: str, fh: int, data: list[float]
) -> Forecast:
    forecast = Forecast(
        model=model, fh=fh, data=data, created_at=datetime.now().isoformat()
    )
    db.add(forecast)
    await db.commit()
    await db.refresh(forecast)
    return forecast


async def get_forecast_by_id(db: AsyncSession, forecast_id: int) -> Forecast | None:
    result = await db.execute(select(Forecast).filter(Forecast.id == forecast_id))
    return result.scalar_one_or_none()
