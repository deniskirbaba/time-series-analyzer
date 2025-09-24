import matplotlib.pyplot as plt
from api_calls import create_forecast_task, get_all_models, get_forecast_data

import streamlit as st


def show_current_predictions(in_progress_predictions):
    st.subheader("Текущие прогнозы")

    if not in_progress_predictions:
        st.info("Нет активных задач прогнозирования")
        return

    sorted_predictions = sorted(
        in_progress_predictions, key=lambda x: x["time"], reverse=True
    )

    for prediction in sorted_predictions:
        with st.expander(
            f"{prediction['model']} (fh={prediction['fh']}) - {prediction['cost']:.2f} ₽"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Модель:** {prediction['model']}")
                st.write(f"**Горизонт прогноза:** {prediction['fh']}")
            with col2:
                st.write(f"**Стоимость:** {prediction['cost']:.2f} ₽")
                st.write(f"**Время запуска:** {prediction['time']}")

            st.info("Прогноз выполняется...")


def show_prediction_history(successful_predictions, ts_data):
    st.subheader("История прогнозов")

    if not successful_predictions:
        st.info("Нет завершенных прогнозов")
        return

    sorted_predictions = sorted(
        successful_predictions, key=lambda x: x["time"], reverse=True
    )

    for i, prediction in enumerate(sorted_predictions):
        with st.expander(
            f"{prediction['model']} (fh={prediction['fh']}) - {prediction['cost']:.2f} ₽"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Модель:** {prediction['model']}")
                st.write(f"**Горизонт прогноза:** {prediction['fh']}")
            with col2:
                st.write(f"**Стоимость:** {prediction['cost']:.2f} ₽")
                st.write(f"**Время выполнения:** {prediction['time']}")

            forecasting_ts_ids = ts_data.get("forecasting_ts", [])
            if forecasting_ts_ids:
                # Simply get the most recent forecast data that matches this prediction
                forecast_data = None
                for forecast_id in reversed(forecasting_ts_ids):
                    try:
                        forecast_data = get_forecast_data(
                            st.session_state.access_token, forecast_id
                        )
                        if (
                            forecast_data
                            and forecast_data.get("model") == prediction["model"]
                            and forecast_data.get("fh") == prediction["fh"]
                        ):
                            break
                    except Exception:
                        continue

                if forecast_data:
                    try:
                        original_data = ts_data.get("data", [])
                        forecast_values = forecast_data.get("data", [])

                        fig, ax = plt.subplots(figsize=(12, 6))

                        x_orig = range(len(original_data))
                        ax.plot(
                            x_orig,
                            original_data,
                            label="Исходные данные",
                            color="blue",
                            linewidth=1.5,
                        )

                        x_forecast = range(
                            len(original_data),
                            len(original_data) + len(forecast_values),
                        )
                        ax.plot(
                            x_forecast,
                            forecast_values,
                            label=f'Прогноз ({prediction["model"]})',
                            color="red",
                            linewidth=2,
                            linestyle="--",
                        )

                        ax.set_xlabel("Временной индекс")
                        ax.set_ylabel("Значение")
                        ax.set_title(
                            f'Прогноз модели {prediction["model"]} (FH={prediction["fh"]})'
                        )
                        ax.legend()
                        ax.grid(True, alpha=0.3)

                        st.pyplot(fig)
                        plt.close()
                    except Exception as e:
                        st.warning(f"Ошибка при отображении графика: {str(e)}")
                else:
                    st.info("Данные прогноза не найдены или еще не готовы")
            else:
                st.info("Прогнозы для этого временного ряда отсутствуют")


def show_failed_predictions(failed_predictions):
    st.subheader("Неудачные прогнозы")

    if not failed_predictions:
        st.info("Нет неудачных прогнозов")
        return

    sorted_predictions = sorted(
        failed_predictions, key=lambda x: x["time"], reverse=True
    )

    for prediction in sorted_predictions:
        with st.expander(
            f"{prediction['model']} (fh={prediction['fh']}) - {prediction['cost']:.2f} ₽ (возвращено)"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Модель:** {prediction['model']}")
                st.write(f"**Горизонт прогноза:** {prediction['fh']}")
            with col2:
                st.write(f"**Стоимость (возвращена):** {prediction['cost']:.2f} ₽")
                st.write(f"**Время неудачи:** {prediction['time']}")

            st.error("Прогноз завершился с ошибкой. Средства возвращены на баланс.")


def show_order_prediction_form(ts_id, user_balance):
    st.subheader("Заказать прогноз")

    models_data = get_all_models(st.session_state.access_token)
    if not models_data:
        st.error("Не удалось загрузить список моделей")
        return

    st.write("**Параметры прогноза:**")

    model_names = [model["name"] for model in models_data]
    selected_model_name = st.selectbox("Выберите модель:", model_names)
    selected_model = next(
        (m for m in models_data if m["name"] == selected_model_name), None
    )

    fh = st.number_input(
        "Горизонт прогноза (количество точек):",
        min_value=1,
        max_value=100,
        value=10,
    )

    if selected_model:
        cost = selected_model["tariffs"] * fh
        st.metric("Стоимость прогноза:", f"{cost:.2f} ₽")

        if cost > user_balance:
            st.error(
                f"Недостаточно средств! Необходимо: {cost:.2f} ₽, доступно: {user_balance:.2f} ₽"
            )
            st.info("Пополните баланс в личном кабинете")
            can_order = False
        else:
            st.success(f"После заказа останется: {user_balance - cost:.2f} ₽")
            can_order = True
    else:
        can_order = False
        cost = 0

    if st.button("Заказать прогноз", disabled=not can_order, type="primary"):
        if can_order and selected_model:
            success, result = create_forecast_task(
                st.session_state.access_token, ts_id, selected_model["name"], fh, cost
            )

            if success:
                st.success(
                    "Прогноз успешно заказан! Обновите страницу через несколько минут для просмотра результатов."
                )
                st.rerun()
            else:
                st.error(f"Ошибка при заказе прогноза: {result}")
