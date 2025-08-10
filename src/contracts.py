from typing import List, Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class UserRegistration(BaseModel):
    login: str
    password: str
    name: str


class UserResponse(BaseModel):
    id: int
    login: str
    name: str
    balance: float
    time_series: List[int]  # list of time series ids


class TimeSeriesData(BaseModel):
    timestamp: str
    value: float


class TimeSeriesCreate(BaseModel):
    data: List[TimeSeriesData]


class TimeSeriesResponse(BaseModel):
    id: int
    data: List[dict]

    class Config:
        from_attributes = True
