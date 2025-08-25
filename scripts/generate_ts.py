from uuid import uuid4

import numpy as np
import pandas as pd


def generate_time_series(length) -> pd.DataFrame:
    index = np.arange(length)

    trend = np.random.uniform(0, 1) * index
    seasonality = np.random.randint(1, 10) * np.sin(
        2 * np.pi * index / np.random.randint(1, 50)
    )
    noise = np.random.normal(0, 2, length)
    target = np.random.randint(1, 100) + trend + seasonality + noise

    df = pd.DataFrame({"index": index, "target": target})

    return df


if __name__ == "__main__":
    ts_df = generate_time_series(np.random.randint(50, 100_000))
    ts_df.to_csv(f"{uuid4()}.csv", index=False)
