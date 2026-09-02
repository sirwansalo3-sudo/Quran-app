import streamlit as st
import sqlite3
import pandas as pd

# 1. بنکەی دراوە (Database)
def get_db_connection():
    conn = sqlite3.connect('quran_center_web.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, full_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_code TEXT UNIQUE, full_name TEXT, username TEXT UNIQUE, password TEXT, assigned_classes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (student_code TEXT PRIMARY KEY, full_name TEXT, level_type TEXT, class_num INTEGER, address TEXT, phone TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS grades (id INTEGER PRIMARY KEY AUTOINCREMENT, student_code TEXT, subject_name TEXT, term INTEGER, daily_score REAL, exam_score REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS teacher_hifz (id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_id INTEGER, surah_or_juz TEXT, daily_score REAL, date TEXT)''')
    
    # زیادرکردنی بەڕێوەبەری سەرەکی ئەگەر بوونی نەبێت
    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO admins (username, password, full_name) VALUES ('admin', 'admin123', 'بەڕێوەبەری سەرەکی')")
    conn.commit()
    conn.close()

init_db()

# 2. ڕێکخستنی پەڕەی Streamlit
st.set_page_config(page_title="سیستەمی بنکەی قورئان", layout="wide")

st.markdown("""
    <style>
    body, div, input, label, h1, h2, h3, p {
        direction: RTL;
        text-align: right;
        font-family: 'Tahoma', 'Segoe UI', sans-serif;
    }
    .stApp {
        background-color: #f9fbfd;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_info = None

# 3. پەڕەی چوونەژوورەوە
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

# 4. بەشی گۆڕینی پاسۆورد
def change_password_section():
    st.subheader("🔑 گۆڕینی وشەی نهێنی (Password)")
    
    with st.form("change_pwd_form"):
        current_pwd = st.text_input("وشەی نهێنی کۆن", type="password")
        new_pwd = st.text_input("وشەی نهێنی نوێ", type="password")
        confirm_pwd = st.text_input("دووبارەکردنەوەی وشەی نهێنی نوێ", type="password")
        submit_pwd = st.form_submit_button("نوێکردنەوەی پاسۆورد")
        
        if submit_pwd:
            if new_pwd != confirm_pwd:
                st.error("وشەی نهێنی نوێ لەگەڵ دووبارەکردنەوەکەی یەکناگرێتەوە!")
                return
                
            if not new_pwd:
                st.error("تکایە وشەی نهێنی نوێ بنووسە!")
                return
                
            conn = get_db_connection()
            c = conn.cursor()
            
            user_id = st.session_state.user_info['id']
            role = st.session_state.role
            table_name = "admins" if role == "Admin" else "teachers"
            
            c.execute(f"SELECT password FROM {table_name} WHERE id=?", (user_id,))
            db_pwd = c.fetchone()[0]
            
            if db_pwd != current_pwd:
                st.error("وشەی نهێنی کۆن هەڵەیە!")
                conn.close()
                return
                
            c.execute(f"UPDATE {table_name} SET password=? WHERE id=?", (new_pwd, user_id))
            conn.commit()
            conn.close()
            st.success("وشەی نهێنی بە سەرکەوتوویی گۆڕدرا!")

# 5. دەستەی بەڕێوەبەر (Admin Panel)
def admin_dashboard():
    st.title(f"👑 بەخێربێیت {st.session_state.user_info['full_name']}")
    if st.button("دەرچوون (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    menu = ["تۆمارکردنی مامۆستا", "تۆمارکردنی نمرەی لەبەرکردنی مامۆستا", "گۆڕینی وشەی نهێنی"]
    choice = st.sidebar.selectbox("بەشەکان", menu)
    
    conn = get_db_connection()
    c = conn.cursor()

    if choice == "تۆمارکردنی مامۆستا":
        st.subheader("تۆمارکردنی مامۆستای نوێ")
        code = st.text_input("کۆدی مامۆستا")
        name = st.text_input("ناوی تەواوی مامۆستا")
        uname = st.text_input("ناوی بەکارهێنەر (Username)")
        pwd = st.text_input("وشەی نهێنی (Password)", type="password")
        classes = st.text_input("پۆلە سپێردراوەکان (وەک: 1, 2, 7)")
        
        if st.button("زیادکردنی مامۆستا"):
            try:
                c.execute("INSERT INTO teachers (teacher_code, full_name, username, password, assigned_classes) VALUES (?,?,?,?,?)",
                          (code, name, uname, pwd, classes))
                conn.commit()
                st.success("مامۆستا بە سەرکەوتوویی زیادکرا!")
            except Exception as e:
                st.error(f"هەڵە: {e}")

        st.divider()
        st.subheader("لیستی مامۆستایان")
        df_teachers = pd.read_sql_query("SELECT teacher_code, full_name, username, assigned_classes FROM teachers", conn)
        st.dataframe(df_teachers, use_container_width=True)

    elif choice == "تۆمارکردنی نمرەی لەبەرکردنی مامۆستا":
        st.subheader("تۆمارکردنی نمرەی لەبەرکردنی قورئانی مامۆستایان")
        c.execute("SELECT id, full_name FROM teachers")
        teachers_list = {row["full_name"]: row["id"] for row in c.fetchall()}
        
        if teachers_list:
            selected_teacher = st.selectbox("مامۆستا هەڵبژێرە", list(teachers_list.keys()))
            surah = st.text_input("سوورەت / جوزء")
            score = st.number_input("نمرەی ڕۆژانە (لە سەر 5)", min_value=0.0, max_value=5.0, step=0.5)
            date = st.date_input("ڕێکەوت")
            
            if st.button("تۆمارکردنی نمرە"):
                c.execute("INSERT INTO teacher_hifz (teacher_id, surah_or_juz, daily_score, date) VALUES (?,?,?,?)",
                          (teachers_list[selected_teacher], surah, score, str(date)))
                conn.commit()
                st.success("نمرەی مامۆستا تۆمارکرا!")
        else:
            st.info("هیچ مامۆستایەک تۆمار نەکراوە.")

    elif choice == "گۆڕینی وشەی نهێنی":
        change_password_section()

    conn.close()

# 6. دەستەی مامۆستا (Teacher Panel)
def teacher_dashboard():
    teacher_info = st.session_state.user_info
    st.title(f"👨‍🏫 بەخێربێیت مامۆستا: {teacher_info['full_name']}")
    if st.button("دەرچوون (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    assigned_classes = [c.strip() for c in teacher_info['assigned_classes'].split(",") if c.strip()]
    st.info(f"پۆلە ڕێگەپێدراوەکانی تۆ: {', '.join(assigned_classes)}")

    menu = ["تۆمارکردنی قوتابی", "بینینی نمرەکانی خۆم", "گۆڕینی وشەی نهێنی"]
    choice = st.sidebar.selectbox("بەشەکان", menu)
    
    conn = get_db_connection()
    c = conn.cursor()

    if choice == "تۆمارکردنی قوتابی":
        st.subheader("زیادکردنی قوتابی")
        code = st.text_input("کۆدی قوتابی")
        name = st.text_input("ناوی تەواوی قوتابی")
        cls = st.selectbox("پۆل", assigned_classes)
        level = "teaching" if int(cls) <= 6 else "hifz"
        addr = st.text_input("شوێنی دانیشتن")
        phone = st.text_input("ژمارەی مۆبایل")

        if st.button("تۆمارکردن"):
            try:
                c.execute("INSERT INTO students VALUES (?,?,?,?,?,?)", (code, name, level, int(cls), addr, phone))
                conn.commit()
                st.success("قوتابی بە سەرکەوتوویی تۆمارکرا!")
            except Exception as e:
                st.error(f"هەڵە: {e}")

    elif choice == "بینینی نمرەکانی خۆم":
        st.subheader("نمرەکانی لەبەرکردنی قورئانی خۆت")
        df_my_scores = pd.read_sql_query("SELECT surah_or_juz as 'سوورەت', daily_score as 'نمرە', date as 'ڕێکەوت' FROM teacher_hifz WHERE teacher_id=?", 
                                         conn, params=(teacher_info['id'],))
        st.dataframe(df_my_scores, use_container_width=True)

    elif choice == "گۆڕینی وشەی نهێنی":
        change_password_section()

    conn.close()

# 7. بەڕێوەبردنی سەرەکی
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Admin":
        admin_dashboard()
    else:
        teacher_dashboard()

