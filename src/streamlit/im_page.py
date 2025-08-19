import os
import sys
import tempfile
from datetime import datetime

from api_calls import (
    create_time_series,
    delete_time_series,
    get_time_series,
    get_user_info,
    top_up_balance,
)

import streamlit as st

sys.path.append("..")
from ts.validate_series import TimeSeriesValidationError, validate_time_series

st.markdown("# Личный кабинет")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

if not st.session_state.authenticated or not st.session_state.access_token:
    st.warning("Вы не авторизованы!")
    st.info(
        "Пожалуйста, войдите в систему или зарегистрируйтесь для доступа к личному кабинету."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Перейти к входу", use_container_width=True):
            st.switch_page("login_page.py")
    with col2:
        if st.button("Перейти к регистрации", use_container_width=True):
            st.switch_page("register_page.py")
else:
    _, _, _, _, refresh_container = st.columns(5)
    with refresh_container:
        if st.button("🔄 Обновить", help="Обновить информацию о пользователе"):
            with st.spinner("Обновление данных..."):
                updated_info = get_user_info(st.session_state.access_token)
                if updated_info:
                    st.session_state.user_info = updated_info
                    st.rerun()
                else:
                    st.error("Ошибка обновления данных")

    if st.session_state.user_info:
        user = st.session_state.user_info

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Имя", user.get("name", "N/A"))
        with col2:
            st.metric("Логин", user.get("login", "N/A"))

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Баланс", f"{user.get('balance', 0):.2f} ₽")
        with col2:
            if st.button("Пополнить баланс", use_container_width=True):
                st.session_state.show_topup_modal = True

        if "show_topup_modal" not in st.session_state:
            st.session_state.show_topup_modal = False

        if st.session_state.show_topup_modal:
            with st.container():
                st.markdown("### Пополнение баланса")

                with st.form("topup_form"):
                    amount = st.number_input(
                        "Сумма пополнения (₽)",
                        min_value=0.01,
                        max_value=100000.0,
                        value=100.0,
                        step=0.01,
                        format="%.2f",
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        submit_button = st.form_submit_button(
                            "Пополнить", use_container_width=True
                        )
                    with col2:
                        cancel_button = st.form_submit_button(
                            "Отмена", use_container_width=True
                        )

                    if submit_button:
                        if amount > 0:
                            with st.spinner("Пополнение баланса..."):
                                result = top_up_balance(
                                    st.session_state.access_token, amount
                                )
                                if result:
                                    st.session_state.user_info = result
                                    st.session_state.show_topup_modal = False
                                    st.success(
                                        f"Баланс успешно пополнен на {amount:.2f} ₽!"
                                    )
                                    st.rerun()
                                else:
                                    st.error("Ошибка при пополнении баланса")
                        else:
                            st.error("Сумма должна быть больше 0")

                    if cancel_button:
                        st.session_state.show_topup_modal = False
                        st.rerun()

        st.markdown("---")
        st.subheader("Временные ряды")

        st.markdown("#### Загрузка временного ряда")
        with st.expander("Требования к структуре временного ряда", expanded=False):
            with open("../data/time_series_requirements.txt", "r") as f:
                st.markdown(f.read())

        uploaded_file = st.file_uploader(
            "Выберите CSV файл с временным рядом",
            type=["csv"],
            help="Загрузите CSV файл с временным рядом согласно требованиям выше",
        )

        if uploaded_file is not None:
            try:
                with tempfile.NamedTemporaryFile(suffix=".csv") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                    with st.spinner("Проверка временного ряда..."):
                        validated_df = validate_time_series(tmp_file_path)
                st.success("Временный ряд успешно загружен и проверен.")

                st.markdown("**Предварительный просмотр данных:**")
                st.dataframe(validated_df.head(5))
                st.text(f"Количество наблюдений: {len(validated_df)}")

                ts_name = st.text_input(
                    "Название временного ряда",
                    placeholder="Введите название для временного ряда",
                )

                if st.button("Сохранить временный ряд", type="primary"):
                    if ts_name.strip():
                        try:
                            ts_data = {
                                "name": ts_name.strip(),
                                "user_id": user.get("id"),
                                "data": validated_df["target"].tolist(),
                            }
                            with st.spinner("Сохранение временного ряда..."):
                                result = create_time_series(
                                    st.session_state.access_token, ts_data
                                )
                                if result:
                                    st.success(
                                        f"Временный ряд '{ts_name}' успешно сохранен."
                                    )
                                    updated_info = get_user_info(
                                        st.session_state.access_token
                                    )
                                    if updated_info:
                                        st.session_state.user_info = updated_info
                                    st.rerun()
                                else:
                                    st.error("Ошибка при сохранении временного ряда.")
                        except Exception as e:
                            st.error(f"Ошибка при сохранении: {str(e)}.")
                    else:
                        st.error("Пожалуйста, введите название для временного ряда.")

            except TimeSeriesValidationError as e:
                st.error(f"Ошибка валидации: {str(e)}.")
            except Exception as e:
                st.error(f"Неожиданная ошибка: {str(e)}.")

        st.markdown("---")
        st.markdown("#### Мои временные ряды")
        time_series_ids = user.get("time_series", [])

        if time_series_ids:
            st.info(f"Количество временных рядов: {len(time_series_ids)}")

            for i, ts_id in enumerate(time_series_ids, 1):
                with st.container():
                    st.markdown(f"##### Временной ряд #{i}")

                    ts_details = get_time_series(st.session_state.access_token, ts_id)

                    if ts_details:
                        size_bytes = (
                            ts_details.get("length", 0) * 4
                        )  # assuming that each value is in 32 bit
                        size_mb = size_bytes / (1024 * 1024)

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Название", ts_details.get("name", "N/A"))
                        with col2:
                            st.metric("Длина", ts_details.get("length", 0))
                        with col3:
                            created_at = ts_details.get("created_at", "N/A")
                            if created_at != "N/A":
                                try:
                                    dt = datetime.fromisoformat(
                                        created_at.replace("Z", "+00:00")
                                    )
                                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                                except:
                                    formatted_date = created_at
                            else:
                                formatted_date = "N/A"
                            st.metric("Создан", formatted_date)
                        with col4:
                            st.metric("Размер", f"{size_mb:.4f} MB")

                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button(f"Исследовать", key=f"explore_{ts_id}"):
                                st.info(
                                    "Функция исследования временного ряда будет добавлена позже"
                                )
                        with col2:
                            if st.button(
                                f"Удалить", key=f"delete_{ts_id}", type="secondary"
                            ):
                                with st.spinner("Удаление временного ряда..."):
                                    success = delete_time_series(
                                        st.session_state.access_token,
                                        ts_id,
                                        user.get("id"),
                                    )
                                    if success:
                                        st.success(
                                            f"Временной ряд '{ts_details.get('name', 'N/A')}' успешно удален!"
                                        )
                                        updated_info = get_user_info(
                                            st.session_state.access_token
                                        )
                                        if updated_info:
                                            st.session_state.user_info = updated_info
                                        st.rerun()
                                    else:
                                        st.error("Ошибка при удалении временного ряда")
                    else:
                        st.error(
                            f"Не удалось загрузить информацию о временном ряду ID: {ts_id}"
                        )

                    st.markdown("---")
        else:
            st.info("У вас пока нет временных рядов")

        st.markdown("---")
        with st.expander("Информация о сессии"):
            st.write(
                f"**Статус авторизации:** {'✅ Авторизован' if st.session_state.authenticated else '❌ Не авторизован'}"
            )
            st.write(
                f"**Токен доступа:** {'✅ Присутствует' if st.session_state.access_token else '❌ Отсутствует'}"
            )
            st.write(
                f"**Время последнего обновления:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

    else:
        st.error("Не удалось загрузить информацию о пользователе")
        if st.button("Попробовать снова"):
            st.rerun()
