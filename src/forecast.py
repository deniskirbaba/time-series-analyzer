import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from statsforecast.models import (
    AutoARIMA,
    AutoETS,
    AutoTBATS,
    AutoTheta,
    HistoricAverage,
)


class LinearTrendModel:
    def fit(self, y, X=None):
        self.n = len(y)
        self.model = LinearRegression()
        self.model.fit(np.arange(self.n).reshape(-1, 1), y)
        return self

    def predict(self, h, X=None):
        future_idx = np.arange(self.n, self.n + h)
        return {"mean": self.model.predict(future_idx.reshape(-1, 1))}


NAIVE_MODELS = {"historic_average": HistoricAverage, "linear_trend": LinearTrendModel}
STATS_MODELS = {"arima": AutoARIMA, "ets": AutoETS, "tbats": AutoTBATS, "theta": AutoTheta}
ALL_MODELS = {**NAIVE_MODELS, **STATS_MODELS}


def train_model(model_name: str, series: pd.DataFrame):
    if model_name not in ALL_MODELS:
        raise ValueError(f"Unknown model: {model_name}")

    model_class = ALL_MODELS[model_name]
    if model_name == "tbats":
        model = model_class(season_length=[7, 30, 120, 365])
    else:
        model = model_class()
    model.fit(series["target"].values)

    return model


def forecast(model, horizon: int):
    if isinstance(model, tuple(ALL_MODELS.values())):
        return model.predict(h=horizon)["mean"]
    else:
        raise TypeError(f"Unknown model type: {type(model)}")
