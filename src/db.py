from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from data_models import Base, TimeSeries, User

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

_DB_INITIALIZED = False  # DB init flag


async def init_db():
    global _DB_INITIALIZED
    if not _DB_INITIALIZED:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        _DB_INITIALIZED = True


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


async def create_time_series(
    db: AsyncSession, user_id: int, data: list[float]
) -> TimeSeries:
    db_ts = TimeSeries(user_id=user_id, data=data)
    db.add(db_ts)
    await db.commit()
    await db.refresh(db_ts)
    return db_ts


async def get_time_series_by_id(db: AsyncSession, id: int) -> TimeSeries | None:
    result = await db.execute(select(TimeSeries).filter(TimeSeries.id == id))
    return result.scalar_one_or_none()


async def update_user_balance(
    db: AsyncSession, user_id: int, amount: float
) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user:
        user.balance += amount
        await db.commit()
        await db.refresh(user)
    return user
