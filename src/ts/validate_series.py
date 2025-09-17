import pandas as pd

EXPECTED_COLUMNS = {"index", "target"}
MIN_OBSERVATIONS = 50
MAX_OBSERVATIONS = 5_000


class TimeSeriesValidationError(Exception):
    pass


def validate_time_series(file_path):
    if not file_path.lower().endswith(".csv"):
        raise TimeSeriesValidationError("File must be in .csv format.")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise TimeSeriesValidationError(f"Failed to read CSV: {e}")
    if set(df.columns) != EXPECTED_COLUMNS:
        raise TimeSeriesValidationError(f"CSV must have columns: {EXPECTED_COLUMNS}.")
    if df.isnull().any().any():
        raise TimeSeriesValidationError("Time series contains missing (NaN) values.")
    if not pd.api.types.is_integer_dtype(df["index"]):
        raise TimeSeriesValidationError("'index' column must be of integer type.")
    if (df["index"] < 0).any():
        raise TimeSeriesValidationError(
            "'index' column must have only non-negative integers."
        )
    if not df["index"].is_unique:
        raise TimeSeriesValidationError("'index' column must have unique values.")
    if not df["index"].is_monotonic_increasing:
        raise TimeSeriesValidationError("'index' column must be in ascending order.")
    if not pd.api.types.is_numeric_dtype(df["target"]):
        raise TimeSeriesValidationError("'target' column must be numeric.")
    n_obs = len(df)
    if n_obs < MIN_OBSERVATIONS:
        raise TimeSeriesValidationError(
            f"Time series must have at least {MIN_OBSERVATIONS} observations."
        )
    if n_obs > MAX_OBSERVATIONS:
        raise TimeSeriesValidationError(
            f"Time series must have at most {MAX_OBSERVATIONS:,} observations."
        )
    return df
