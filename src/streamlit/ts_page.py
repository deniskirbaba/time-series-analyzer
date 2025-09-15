import sys
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from api_calls import (
    get_all_models,
    get_analysis_task_status,
    get_time_series,
    start_analysis_task,
)

import streamlit as st

sys.path.append("..")

st.markdown("# Анализ и предсказание временного ряда")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "selected_ts_id" not in st.session_state:
    st.session_state.selected_ts_id = None

# Not authorized logic
if not st.session_state.authenticated or not st.session_state.access_token:
    st.warning("Вы не авторизованы!")
    st.info("Пожалуйста, войдите в систему для доступа к анализу временных рядов.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Перейти к входу", use_container_width=True):
            st.switch_page("login_page.py")
    with col2:
        if st.button("Перейти к регистрации", use_container_width=True):
            st.switch_page("register_page.py")
    st.stop()

# Authorized logic
if not st.session_state.selected_ts_id:
    st.warning("Временной ряд не выбран!")
    st.info("Пожалуйста, выберите временной ряд для анализа в личном кабинете.")

    if st.button("Вернуться в личный кабинет", use_container_width=True):
        st.switch_page("im_page.py")
    st.stop()

ts_id = st.session_state.selected_ts_id
ts_data = get_time_series(st.session_state.access_token, ts_id)

if not ts_data:
    st.error(
        "Не удалось загрузить данные временного ряда, попробуйте выбрать данный временной ряд еще раз в личном кабинете."
    )
    if st.button("Вернуться в личный кабинет", use_container_width=True):
        st.switch_page("im_page.py")
    st.stop()

_, _, _, _, refresh_container = st.columns(5)
with refresh_container:
    if st.button("🔄 Обновить"):
        st.rerun()

st.markdown("---")
st.subheader("Информация о временном ряде")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Название", ts_data.get("name", "N/A"))
with col2:
    st.metric("Длина", ts_data.get("length", 0))
with col3:
    created_at = ts_data.get("created_at", "N/A")
    if created_at != "N/A":
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            formatted_date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_date = created_at
    else:
        formatted_date = "N/A"
    st.metric("Создан", formatted_date)
with col4:
    size_bytes = ts_data.get("length", 0) * 4  # assuming 32-bit floats
    size_mb = size_bytes / (1024 * 1024)
    st.metric("Размер", f"{size_mb:.4f} MB")

st.markdown("#### График временного ряда")
data_values = ts_data.get("data", [])
if data_values:
    df = pd.DataFrame(
        {"Временной индекс": range(len(data_values)), "Значение": data_values}
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["Временной индекс"], df["Значение"], linewidth=1.5, color="#1f77b4")
    ax.set_xlabel("Временной индекс")
    ax.set_ylabel("Значение")
    ax.set_title(f"Временной ряд: {ts_data.get('name', 'N/A')}")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close()
else:
    st.warning("Нет данных для отображения графика")

st.markdown("---")
st.subheader("Анализ временного ряда")

analysis_results = ts_data.get("analysis_results", {})
has_analysis = bool(analysis_results and analysis_results != {})

task_status = get_analysis_task_status(st.session_state.access_token, ts_id)

with st.expander("Информация об анализе", expanded=False):
    with open("../data/time_series_analysis_info.txt", "r") as f:
        st.markdown(f.read())

if has_analysis:
    st.success("Анализ выполнен")

    with st.expander("Результаты анализа", expanded=True):
        if isinstance(analysis_results, dict) and "error" not in analysis_results:
            st.subheader("Основные статистики")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Среднее", f"{analysis_results['mean']:.3f}")
                st.metric("Медиана", f"{analysis_results['median']:.3f}")
            with col2:
                st.metric("Стд. отклонение", f"{analysis_results['std']:.3f}")
            with col3:
                st.metric("Минимум", f"{analysis_results['min']:.3f}")
                st.metric("Максимум", f"{analysis_results['max']:.3f}")
            with col4:
                st.metric("25-й процентиль", f"{analysis_results['q25']:.3f}")
                st.metric("75-й процентиль", f"{analysis_results['q75']:.3f}")

            st.subheader("Анализ тренда")
            col1, col2 = st.columns(2)
            p_val = analysis_results["trend_test_p_value"]
            with col1:
                trend_result = analysis_results["trend_test_result"]
                if trend_result == "increasing":
                    st.success(f"Тренд: Возрастающий")
                elif trend_result == "decreasing":
                    st.error(f"Тренд: Убывающий")
                else:
                    st.info(f"Тренд: {trend_result}")
                if p_val < 0.05:
                    st.success("Тренд статистически значим (p < 0.05)")
                else:
                    st.info("Тренд статистически незначим (p ≥ 0.05)")
            with col2:
                st.metric("P-значение (Манн-Кендалл)", f"{p_val:.5f}")

            st.subheader("ARCH-тест (гетероскедастичность)")
            arch_p = analysis_results["arch_test_p_value"]
            col1, col2 = st.columns(2)
            with col1:
                if arch_p < 0.05:
                    st.warning("Обнаружена гетероскедастичность")
                else:
                    st.success("Гомоскедастичность")
            with col2:
                st.metric("ARCH тест p-значение", f"{arch_p:.5f}")

            st.subheader("Частотный анализ")
            freq_data = analysis_results["fourier_freqs"]
            if "frequencies" in freq_data and "amplitudes" in freq_data:
                freq_df = pd.DataFrame(
                    {
                        "Частота": freq_data["frequencies"],
                        "Амплитуда": freq_data["amplitudes"],
                    }
                )
                st.dataframe(freq_df, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Наиболее частые значения")
                most_freq = analysis_results["most_frequent"]
                for value, count in most_freq.items():
                    st.write(f"**{float(value):.3f}**: {count} раз")

            with col2:
                st.subheader("Наименее частые значения")
                least_freq = analysis_results["least_frequent"]
                for value, count in least_freq.items():
                    st.write(f"**{float(value):.3f}**: {count} раз")

            st.subheader("Графики анализа")
            fig, ax = plt.subplots(figsize=(14, 8))
            original_data = ts_data.get("data", [])
            x_axis = range(len(original_data))
            ax.plot(x_axis, original_data, label="Исходный ряд", alpha=0.7, linewidth=1)
            smoothed = analysis_results["smoothed_series"]
            ax.plot(
                x_axis,
                smoothed,
                label="Сглаженный ряд (EWM)",
                linewidth=2,
                color="orange",
            )
            trend = analysis_results["linear_trend"]
            ax.plot(
                x_axis,
                trend,
                label="Линейный тренд",
                linewidth=2,
                color="red",
                linestyle="--",
            )

            ax.set_xlabel("Временной индекс")
            ax.set_ylabel("Значение")
            ax.set_title("Исходный ряд, сглаженный ряд и тренд")
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close()

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

            residuals = analysis_results["residuals"]
            x_axis = range(len(residuals))

            ax1.plot(x_axis, residuals, color="green", alpha=0.8)
            ax1.axhline(y=0, color="red", linestyle="--", alpha=0.7)
            ax1.set_xlabel("Временной индекс")
            ax1.set_ylabel("Остатки")
            ax1.set_title("Остатки после удаления тренда")
            ax1.grid(True, alpha=0.3)

            ax2.hist(residuals, bins=30, alpha=0.7, color="green", edgecolor="black")
            ax2.axvline(x=0, color="red", linestyle="--", alpha=0.7)
            ax2.set_xlabel("Значение остатков")
            ax2.set_ylabel("Частота")
            ax2.set_title("Распределение остатков")
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        elif isinstance(analysis_results, dict) and "error" in analysis_results:
            st.error(f"Ошибка анализа: {analysis_results['error']}")
        else:
            st.write("Результаты анализа:")
            st.write(analysis_results)

elif task_status and task_status.get("has_task"):
    status = task_status.get("status")
    updated_at = task_status.get("updated_at")

    if status == "queued":
        st.info("Анализ поставлен в очередь")
        st.write("Ваш запрос на анализ находится в очереди на выполнение.")

    elif status == "in_progress":
        st.info("Анализ выполняется")
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                st.write(f"Последнее обновление: {formatted_time}")
            except:
                st.write(f"Последнее обновление: {updated_at}")

    elif status == "failed":
        st.error("Анализ завершился с ошибкой")
        st.write(
            "Произошла ошибка при выполнении анализа. Попробуйте запустить анализ заново."
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Повторить анализ", type="primary", use_container_width=True):
                result = start_analysis_task(st.session_state.access_token, ts_id)
                if result:
                    st.success("Анализ запущен повторно!")
                    st.rerun()
                else:
                    st.error("Не удалось запустить анализ")
        with col2:
            st.markdown("*Анализ предоставляется бесплатно*")

    elif status == "done":
        st.warning("Анализ завершен, но результаты не загружены")
        st.write(
            "Анализ был выполнен, но результаты еще не отображаются. Обновите страницу."
        )

else:
    st.info("Анализ не выполнен")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Запустить анализ", type="primary", use_container_width=True):
            result = start_analysis_task(st.session_state.access_token, ts_id)
            if result:
                st.success("Анализ запущен!")
                st.rerun()
            else:
                st.error("Не удалось запустить анализ")
    with col2:
        st.markdown(
            "*Анализ предоставляется бесплатно. Анализ поможет понять структуру временного ряда и подготовить данные для прогнозирования*"
        )

st.markdown("---")
st.subheader("Прогнозирование")

with st.expander("Информация о прогнозировании", expanded=False):
    with open("../data/time_series_forecasting_info.txt", "r") as f:
        st.markdown(f.read())
with st.expander("Доступные модели и тарифы", expanded=False):
    models_data = get_all_models(st.session_state.access_token)
    if models_data:
        for i, model in enumerate(models_data):
            if i != 0:
                st.markdown("---")
            st.markdown(f"##### {model['name']}")
            st.markdown(f"**Описание:** {model['info']}")
            st.markdown(f"**Тариф:** {model['tariffs']} ₽ за точку")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("FH=10", f"{model['tariffs'] * 10:.2f} ₽")
            with col2:
                st.metric("FH=25", f"{model['tariffs'] * 25:.2f} ₽")
            with col3:
                st.metric("FH=50", f"{model['tariffs'] * 50:.2f} ₽")
    else:
        st.error("Не удалось загрузить информацию о моделях")
