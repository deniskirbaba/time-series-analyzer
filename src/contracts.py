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


class TimeSeriesCreate(BaseModel):
    name: str
    user_id: int
    data: list[float]


class TimeSeriesResponse(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: str
    length: int
    data: list[float]
    analysis_results: dict
    forecasting_ts: list[int]


class ModelResponse(BaseModel):
    name: str
    info: str
    tariffs: float
