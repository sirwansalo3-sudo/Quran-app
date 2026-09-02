import streamlit as st
import sqlite3
import pandas as pd

def get_db_connection():
    conn = sqlite3.connect('quran_center_web.db')
    conn.row_factory = sqlite3.Row
    return conn

st.set_page_config(page_title="سیستەمی بنکەی قورئان", layout="wide")

st.markdown("""
    <style>
    body, div, input, label, h1, h2, h3, p {
        direction: RTL;
        text-align: right;
        font-family: 'Tahoma', 'Segoe UI', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_info = None

def login_page():
    st.title("📖 سیستەمی بنکەی قورئان - چوونەژوورەوە")
    with st.form("login_form"):
        username = st.text_input("ناوی بەکارهێنەر")
        password = st.text_input("وشەی نهێنی", type="password")
        submit = st.form_submit_button("چوونەژوورەوە")
        if submit:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
            admin = c.fetchone()
            if admin:
                st.session_state.logged_in = True
                st.session_state.role = "Admin"
                st.session_state.user_info = dict(admin)
                st.rerun()
                return

            c.execute("SELECT * FROM teachers WHERE username=? AND password=?", (username, password))
            teacher = c.fetchone()
            conn.close()
            if teacher:
                st.session_state.logged_in = True
                st.session_state.role = "Teacher"
                st.session_state.user_info = dict(teacher)
                st.rerun()
                return
            st.error("ناوی بەکارهێنەر یان پاسۆورد هەڵەیە!")

def admin_dashboard():
    st.title(f"👑 بەخێربێیت {st.session_state.user_info['full_name']}")
    if st.button("دەرچوون"):
        st.session_state.logged_in = False
        st.rerun()

    menu = ["تۆمارکردنی مامۆستا", "نمرەی لەبەرکردنی مامۆستایان", "لیستی گشتی"]
    choice = st.sidebar.selectbox("بەشەکان", menu)
    conn = get_db_connection()
    c = conn.cursor()

    if choice == "تۆمارکردنی مامۆستا":
        st.subheader("تۆمارکردنی مامۆستای نوێ")
        code = st.text_input("کۆدی مامۆستا")
        name = st.text_input("ناوی تەواوی مامۆستا")
        uname = st.text_input("ناوی بەکارهێنەر")
        pwd = st.text_input("وشەی نهێنی", type="password")
        classes = st.text_input("پۆلەکان (وەک: 1, 2, 7)")

        if st.button("زیادکردن"):
            try:
                c.execute("INSERT INTO teachers (teacher_code, full_name, username, password, assigned_classes) VALUES (?,?,?,?,?)",
                          (code, name, uname, pwd, classes))
                conn.commit()
                st.success("مامۆستا بە سەرکەوتوویی زیادکرا!")
            except Exception as e:
                st.error(f"هەڵە: {e}")

        df_teachers = pd.read_sql_query("SELECT teacher_code, full_name, username, assigned_classes FROM teachers", conn)
        st.dataframe(df_teachers, use_container_width=True)

    conn.close()

def teacher_dashboard():
    teacher_info = st.session_state.user_info
    st.title(f"👨‍🏫 بەخێربێیت مامۆستا: {teacher_info['full_name']}")
    if st.button("دەرچوون"):
        st.session_state.logged_in = False
        st.rerun()

    assigned_classes = [c.strip() for c in teacher_info['assigned_classes'].split(",") if c.strip()]
    st.info(f"پۆلەکانت: {', '.join(assigned_classes)}")

    menu = ["تۆمارکردنی قوتابی"]
    choice = st.sidebar.selectbox("بەشەکان", menu)
    conn = get_db_connection()
    c = conn.cursor()

    if choice == "تۆمارکردنی قوتابی":
        st.subheader("زیادکردنی قوتابی")
        code = st.text_input("کۆدی قوتابی")
        name = st.text_input("ناوی قوتابی")
        cls = st.selectbox("پۆل", assigned_classes)
        level = "teaching" if int(cls) <= 6 else "hifz"
        addr = st.text_input("شوێنی دانیشتن")
        phone = st.text_input("ژمارەی مۆبایل")

        if st.button("تۆمارکردن"):
            try:
                c.execute("INSERT INTO students VALUES (?,?,?,?,?,?)", (code, name, level, int(cls), addr, phone))
                conn.commit()
                st.success("قوتابی تۆمارکرا!")
            except Exception as e:
                st.error(f"هەڵە: {e}")
    conn.close()

if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Admin":
        admin_dashboard()
    else:
        teacher_dashboard()
