from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from data_models import Base, TimeSeries, User

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_login(db: Session, login: str) -> Optional[User]:
    return db.query(User).filter(User.login == login).first()


def get_user_by_id(db: Session, id: int) -> Optional[User]:
    return db.query(User).filter(User.id == id).first()


def create_user(
    db: Session, login: str, hashed_password: str, name: str, balance: float = 0.0
) -> User:
    db_user = User(
        login=login, hashed_password=hashed_password, name=name, balance=balance
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_time_series(db: Session, data: list) -> TimeSeries:
    db_ts = TimeSeries(data=data)
    db.add(db_ts)
    db.commit()
    db.refresh(db_ts)
    return db_ts


def add_time_series_to_user(db: Session, user_id: int, ts_id: int):
    user = get_user_by_id(db, user_id)
    ts = db.query(TimeSeries).filter(TimeSeries.id == ts_id).first()
    if user and ts:
        user.time_series.append(ts)
        db.commit()
        return True
    return False
