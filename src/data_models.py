from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class User(Base):
    __tablename__ = "users"

    login: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str]
    name: Mapped[str]
    balance: Mapped[float] = mapped_column(Float, default=0.0)

    time_series = relationship(
        "TimeSeries",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TimeSeries(Base):
    __tablename__ = "ts"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str]
    created_at: Mapped[str]
    length: Mapped[int]
    data: Mapped[list[float]] = mapped_column(JSON)
    analysis_results: Mapped[dict] = mapped_column(JSON)
    forecasting_ts: Mapped[list[int]] = mapped_column(JSON)

    user = relationship("User", back_populates="time_series")


class Model(Base):
    __tablename__ = "models"

    name: Mapped[str]
    info: Mapped[str]
    tariffs: Mapped[float]
