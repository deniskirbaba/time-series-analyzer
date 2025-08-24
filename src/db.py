import json
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from data_models import Base, Model, TimeSeries, User

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine
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


async def create_time_series(
    db: AsyncSession, user_id: int, name: str, data: list[float]
) -> TimeSeries:
    from datetime import datetime

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


async def get_time_series_by_id(db: AsyncSession, id: int) -> TimeSeries | None:
    result = await db.execute(select(TimeSeries).filter(TimeSeries.id == id))
    return result.scalar_one_or_none()


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
