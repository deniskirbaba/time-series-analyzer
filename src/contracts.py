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
    time_series: list[int]  # list of time series ids


class TimeSeries(BaseModel):
    id: int
    user_id: int
    data: list[float]
