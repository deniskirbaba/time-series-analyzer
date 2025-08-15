from api_calls import get_user_info, login_user

import streamlit as st

st.markdown("# Вход")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

if st.session_state.authenticated:
    st.success("Вы уже авторизованы!")
    st.info("Перейдите в личный кабинет для просмотра информации о профиле.")

else:
    with st.form("login_form"):
        st.subheader("Войдите в систему")

        username = st.text_input("Логин", placeholder="Введите ваш логин")
        password = st.text_input(
            "Пароль", type="password", placeholder="Введите ваш пароль"
        )

        submitted = st.form_submit_button("Войти")

        if submitted:
            if not username or not password:
                st.error("Пожалуйста, заполните все поля")
            else:
                with st.spinner("Выполняется вход..."):
                    token_data = login_user(username, password)

                    if token_data:
                        st.session_state.access_token = token_data["access_token"]

                        user_info = get_user_info(token_data["access_token"])
                        if user_info:
                            st.session_state.user_info = user_info
                            st.session_state.authenticated = True
                            st.success("Успешный вход в систему!")
                            st.switch_page("im_page.py")
                        else:
                            st.error("Ошибка получения информации о пользователе")
                    else:
                        st.error("Неверный логин или пароль")
