import logging

from ts.analyze import analyze_time_series
from ts.forecast import forecast, train_model


def task_analyze_time_series(ts_data: list[float], task_id: str):
    logging.info(f"Starting analysis for task {task_id}")
    try:
        if not ts_data or not isinstance(ts_data, list):
            raise ValueError("Invalid time series data provided")
        analysis_results = analyze_time_series(ts_data)
        logging.info(f"Analysis completed successfully for task {task_id}")
        return {"success": True, "task_id": task_id, "results": analysis_results}

    except Exception as e:
        logging.error(f"Analysis failed for task {task_id}: {str(e)}")
        return {"success": False, "task_id": task_id, "error": str(e)}
