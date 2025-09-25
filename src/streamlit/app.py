import streamlit as st

st.set_page_config(
    page_title="Time Series Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

login_page = st.Page("login_page.py", title="Вход")
register_page = st.Page("register_page.py", title="Регистрация")
im_page = st.Page("im_page.py", title="Личный кабинет")
ts_page = st.Page("ts_page.py", title="Анализ/Предсказание")
ts_loader_page = st.Page("ts_loader_page.py", title="Загрузка")

pg = st.navigation(
    {
        "Авторизация": [login_page, register_page],
        "Аккаунт": [im_page],
        "Временные ряды": [ts_page, ts_loader_page],
    }
)

with st.sidebar:
    st.markdown("### Time Series Analyzer")
    st.markdown("Сервис для анализа и предсказания временных рядов")

    if st.session_state.authenticated and st.session_state.user_info:
        st.success("✅ Авторизован")
        st.write(f"**Пользователь:** {st.session_state.user_info.get("name", "N/A")}")
        st.write(f"**Логин:** {st.session_state.user_info.get("login", "N/A")}")
        st.write(f"**Баланс:** {st.session_state.user_info.get("balance", "N/A")} ₽")

        if st.button("Выйти", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.user_info = None
            st.rerun()
    else:
        st.warning("❌ Не авторизован")

pg.run()
