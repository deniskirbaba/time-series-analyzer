from datetime import datetime

from api_calls import get_user_info, top_up_balance

import streamlit as st

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
        time_series = user.get("time_series", [])

        if time_series:
            st.info(f"У вас есть {len(time_series)} временных рядов")

            with st.expander("Просмотреть ID временных рядов"):
                for i, ts_id in enumerate(time_series, 1):
                    st.write(f"{i}. Временной ряд ID: {ts_id}")
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
