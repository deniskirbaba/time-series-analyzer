import sys
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from api_calls import get_model, get_time_series

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

with st.expander("Информация об анализе", expanded=False):
    with open("../data/time_series_analysis_info.txt", "r") as f:
        st.markdown(f.read())

if has_analysis:
    st.success("Анализ выполнен")
else:
    st.info("Анализ не выполнен")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Запустить анализ", type="primary", use_container_width=True):
            st.info("Функция анализа будет реализована в следующих версиях")
    with col2:
        st.markdown(
            "*Анализ предоставляется бесплатно. Анализ поможет понять структуру временного ряда и подготовить данные для прогнозирования*"
        )

st.markdown("---")
st.subheader("Прогнозирование")
