import numpy as np
import pandas as pd
import pymannkendall as mk
from statsmodels.stats.diagnostic import het_arch


def get_simple_stats(series: pd.Series) -> dict:
    desc = series.describe(percentiles=[0.25, 0.75])
    stats = {
        "mean": desc["mean"],
        "median": desc["50%"],
        "std": desc["std"],
        "q25": desc["25%"],
        "q75": desc["75%"],
        "min": desc["min"],
        "max": desc["max"],
        "most_frequent": series.value_counts().nlargest(3).to_dict(),
        "least_frequent": series.value_counts().nsmallest(3).to_dict(),
    }
    return stats


def get_frequency_analysis(series: pd.Series) -> dict:
    fft_result = np.fft.fft(series.values)
    fft_freq = np.fft.fftfreq(len(series))

    positive_freq_indices = np.where(fft_freq > 0)
    positive_freqs = fft_freq[positive_freq_indices]
    positive_fft_result = np.abs(fft_result[positive_freq_indices])

    sorted_indices = np.argsort(positive_fft_result)[::-1]

    significant_freqs = {
        "frequencies": positive_freqs[sorted_indices[:3]].tolist(),
        "amplitudes": positive_fft_result[sorted_indices[:3]].tolist(),
    }

    return {"fourier_freqs": significant_freqs}


def get_statistical_tests(series: pd.Series) -> dict:
    # Тест Манна-Кендалла
    trend_test = mk.original_test(series)

    # Линейный тренд
    x = np.arange(len(series))
    slope, intercept = np.polyfit(x, series, 1)
    trend_line = slope * x + intercept

    # ARCH-тест
    residuals = series - trend_line
    arch_test = het_arch(residuals)

    return {
        "trend_test_result": trend_test.trend,
        "trend_test_p_value": trend_test.p,
        "linear_trend": trend_line.tolist(),
        "arch_test_stat": arch_test[0],
        "arch_test_p_value": arch_test[1],
        "residuals": residuals.tolist(),
    }


def get_smoothed_series(series: pd.Series) -> dict:
    smoothed = series.ewm(span=12, adjust=False).mean()
    return {"smoothed_series": smoothed.tolist()}


def analyze_time_series(series: list[float]) -> dict:
    """
    Полный анализ временного ряда.
    """
    try:
        series = pd.Series(series)

        results = {}
        results.update(get_simple_stats(series))
        results.update(get_frequency_analysis(series))
        results.update(get_statistical_tests(series))
        results.update(get_smoothed_series(series))

        return results

    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
