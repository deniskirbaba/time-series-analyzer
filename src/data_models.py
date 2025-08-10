from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    balance = Column(Float, default=0.0)

    time_series = relationship("TimeSeries", back_populates="user")


class TimeSeries(Base):
    __tablename__ = "ts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data = Column(
        JSON, nullable=False
    )  # JSONB format: [{"timestamp": "2024-01-01", "value": 10.2}, ...]

    user = relationship("User", back_populates="time_series")
