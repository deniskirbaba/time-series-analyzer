from api_calls import get_user_info, login_user, register_user

import streamlit as st

st.markdown("# Регистрация")


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
    with st.form("registration_form"):
        st.subheader("Создайте новый аккаунт")

        name = st.text_input("Имя", placeholder="Введите ваше имя")
        login = st.text_input("Логин", placeholder="Введите логин для входа")
        password = st.text_input(
            "Пароль", type="password", placeholder="Введите пароль"
        )
        password_confirm = st.text_input(
            "Подтвердите пароль", type="password", placeholder="Повторите пароль"
        )

        submitted = st.form_submit_button("Зарегистрироваться")

        if submitted:
            # Validation
            if not name or not login or not password or not password_confirm:
                st.error("Пожалуйста, заполните все поля")
            elif password != password_confirm:
                st.error("Пароли не совпадают")
            elif len(password) < 6:
                st.error("Пароль должен содержать минимум 6 символов")
            elif len(login) < 3:
                st.error("Логин должен содержать минимум 3 символа")
            else:
                with st.spinner("Создание аккаунта..."):
                    error_response = register_user(login, password, name)

                    if not error_response:
                        st.success("Аккаунт успешно создан!")

                        with st.spinner("Выполняется автоматический вход..."):
                            token_data = login_user(login, password)

                            if token_data:
                                st.session_state.access_token = token_data[
                                    "access_token"
                                ]

                                user_info = get_user_info(token_data["access_token"])
                                if user_info:
                                    st.session_state.user_info = user_info
                                    st.session_state.authenticated = True
                                    st.success("Успешный вход в систему!")
                                    st.switch_page("im_page.py")
                                else:
                                    st.error(
                                        "Ошибка получения информации о пользователе"
                                    )
                            else:
                                st.warning(
                                    "Аккаунт создан, но автоматический вход не удался. Попробуйте войти вручную на странице входа."
                                )
                    else:
                        if "detail" in error_response:
                            if "already exists" in error_response["detail"]:
                                st.error("Пользователь с таким логином уже существует")
                            else:
                                st.error(
                                    f"Ошибка регистрации: {error_response['detail']}"
                                )
                        else:
                            st.error("Произошла ошибка при регистрации")
