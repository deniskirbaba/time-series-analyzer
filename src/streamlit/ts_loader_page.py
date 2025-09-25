import sys

import pandas as pd
from api_calls import (
    get_forecast_data,
    get_forecast_task_status,
    get_time_series,
    get_user_info,
)

import streamlit as st

sys.path.append("..")

st.markdown("# Загрузчик временных рядов")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

if not st.session_state.authenticated or not st.session_state.access_token:
    st.warning("Вы не авторизованы!")
    st.info("Пожалуйста, войдите в систему для доступа к загрузчику временных рядов.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Перейти к входу", use_container_width=True):
            st.switch_page("login_page.py")
    with col2:
        if st.button("Перейти к регистрации", use_container_width=True):
            st.switch_page("register_page.py")
    st.stop()

user_info = get_user_info(st.session_state.access_token)
if not user_info:
    st.error("Не удалось загрузить информацию о пользователе")
    st.stop()

time_series_ids = user_info.get("time_series", [])

if not time_series_ids:
    st.info("У вас пока нет временных рядов")
    if st.button("Перейти в личный кабинет для загрузки", use_container_width=True):
        st.switch_page("im_page.py")
    st.stop()

st.markdown("---")
st.subheader("Выберите временной ряд")

ts_options = {}
ts_names = []

for ts_id in time_series_ids:
    ts_details = get_time_series(st.session_state.access_token, ts_id)
    if ts_details:
        name = ts_details.get("name", f"TS-{ts_id}")
        ts_options[name] = ts_id
        ts_names.append(name)

if not ts_names:
    st.error("Не удалось загрузить информацию о временных рядах")
    st.stop()

selected_ts_name = st.selectbox("Выберите временной ряд:", ts_names)
selected_ts_id = ts_options[selected_ts_name]

ts_data = get_time_series(st.session_state.access_token, selected_ts_id)
if not ts_data:
    st.error("Не удалось загрузить данные временного ряда")
    st.stop()

st.markdown("---")
st.subheader("Скачать данные")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Исходный временной ряд")
    original_data = ts_data.get("data", [])

    if original_data:
        st.success(f"Доступно {len(original_data)} точек")

        # Prepare CSV
        original_csv = pd.DataFrame(
            {"index": range(len(original_data)), "value": original_data}
        ).to_csv(index=False)

        st.download_button(
            label="Скачать исходные данные",
            data=original_csv,
            file_name=f"{ts_data.get('name', 'timeseries')}_original.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("Данные недоступны")

with col2:
    st.markdown("#### EMA обработанный ряд")
    analysis_results = ts_data.get("analysis_results", {})

    if analysis_results and "smoothed_series" in analysis_results:
        smoothed_data = analysis_results["smoothed_series"]
        st.success(f"Доступно {len(smoothed_data)} точек")

        # Prepare CSV
        ema_csv = pd.DataFrame(
            {"index": range(len(smoothed_data)), "value": smoothed_data}
        ).to_csv(index=False)

        st.download_button(
            label="Скачать EMA данные",
            data=ema_csv,
            file_name=f"{ts_data.get('name', 'timeseries')}_ema.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("EMA данные недоступны")
        st.info("Выполните анализ временного ряда")

with col3:
    st.markdown("#### Прогнозированные данные")

    forecast_status = get_forecast_task_status(
        st.session_state.access_token, selected_ts_id
    )
    forecasting_ts_ids = ts_data.get("forecasting_ts", [])

    if forecast_status and forecast_status.get("successful_predictions"):
        successful_predictions = forecast_status.get("successful_predictions", [])

        forecast_options = []
        forecast_data_map = {}

        for i, prediction in enumerate(successful_predictions):
            option_name = (
                f"{prediction['model']} (FH={prediction['fh']}) - {prediction['time']}"
            )
            forecast_options.append(option_name)

            if forecasting_ts_ids:
                for forecast_id in reversed(forecasting_ts_ids):
                    try:
                        temp_forecast_data = get_forecast_data(
                            st.session_state.access_token, forecast_id
                        )
                        if (
                            temp_forecast_data
                            and temp_forecast_data.get("model") == prediction["model"]
                            and temp_forecast_data.get("fh") == prediction["fh"]
                        ):
                            forecast_data_map[option_name] = temp_forecast_data
                            break
                    except Exception:
                        continue

        if forecast_options:
            selected_forecast = st.selectbox(
                "Выберите прогноз для скачивания:",
                forecast_options,
                key="forecast_selector",
            )

            if selected_forecast in forecast_data_map:
                forecast_data = forecast_data_map[selected_forecast]
                forecast_values = forecast_data.get("data", [])

                st.success(f"Доступно {len(forecast_values)} точек")

                selected_prediction = None
                for pred in successful_predictions:
                    option_name = f"{pred['model']} (FH={pred['fh']}) - {pred['time']}"
                    if option_name == selected_forecast:
                        selected_prediction = pred
                        break

                if selected_prediction:
                    st.info(f"Модель: {selected_prediction['model']}")

                original_data = ts_data.get("data", [])
                forecast_csv = pd.DataFrame(
                    {
                        "index": range(
                            len(original_data),
                            len(original_data) + len(forecast_values),
                        ),
                        "value": forecast_values,
                    }
                ).to_csv(index=False)

                st.download_button(
                    label="Скачать прогноз",
                    data=forecast_csv,
                    file_name=f"{ts_data.get('name', 'timeseries')}_forecast_{selected_prediction['model']}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.warning("Данные выбранного прогноза недоступны")
        else:
            st.warning("Данные прогнозов недоступны")
    else:
        st.warning("Прогнозы недоступны")
        st.info("Заказать прогноз в разделе анализа")
