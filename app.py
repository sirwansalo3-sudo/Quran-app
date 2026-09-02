import streamlit as st
import sqlite3
import pandas as pd
from weasyprint import HTML

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
    
    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO admins (username, password, full_name) VALUES ('admin', 'admin123', 'بەڕێوەبەری سەرەکی')")
    conn.commit()
    conn.close()

init_db()

# 2. ڕێکخستنی شێواز و ڕەنگەکان (CSS) بۆ دیاربوونی هەموو خانەکان
st.set_page_config(page_title="سیستەمی بنکەی قورئان", layout="wide")

st.markdown("""
    <style>
    /* چارەسەری ڕەشبوونی خانەکان و ڕوونبوونی نووسینەکان */
    html, body, [class*="css"], div, input, label, select, textarea {
        direction: RTL !important;
        text-align: right !important;
        font-family: 'Segoe UI', Tahoma, sans-serif !important;
        color: #111111 !important;
    }
    .stApp {
        background-color: #ffffff !important;
    }
    input, select, textarea, [data-baseweb="select"] {
        background-color: #f0f2f6 !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        border-radius: 6px !important;
    }
    /* چاککردنی خشتەکان */
    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        color: #000000 !important;
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

def change_password_section():
    st.subheader("🔑 گۆڕینی وشەی نهێنی")
    with st.form("change_pwd_form"):
        current_pwd = st.text_input("وشەی نهێنی کۆن", type="password")
        new_pwd = st.text_input("وشەی نهێنی نوێ", type="password")
        confirm_pwd = st.text_input("دووبارەکردنەوەی وشەی نهێنی نوێ", type="password")
        submit_pwd = st.form_submit_button("نوێکردنەوە")
        
        if submit_pwd:
            if new_pwd != confirm_pwd or not new_pwd:
                st.error("وشەی نهێنی نوێ هەڵەیە یان یەکناگرێتەوە!")
                return
                
            conn = get_db_connection()
            c = conn.cursor()
            user_id = st.session_state.user_info['id']
            table_name = "admins" if st.session_state.role == "Admin" else "teachers"
            
            c.execute(f"SELECT password FROM {table_name} WHERE id=?", (user_id,))
            if c.fetchone()[0] != current_pwd:
                st.error("وشەی نهێنی کۆن هەڵەیە!")
                conn.close()
                return
                
            c.execute(f"UPDATE {table_name} SET password=? WHERE id=?", (new_pwd, user_id))
            conn.commit()
            conn.close()
            st.success("پاسۆورد بە سەرکەوتوویی گۆڕدرا!")

def generate_student_card_pdf(student_info, grades):
    rows_html = ""
    for g in grades:
        total = g['daily_score'] + g['exam_score']
        rows_html += f"""
        <tr>
            <td>{g['subject_name']}</td>
            <td>وەرزی {g['term']}</td>
            <td>{g['daily_score']}</td>
            <td>{g['exam_score']}</td>
            <td><strong>{total}</strong></td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ckb">
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; padding: 20px; color: #2c3e50; }}
            .header {{ text-align: center; border-bottom: 2px solid #2e7d32; padding-bottom: 10px; }}
            .info-box {{ background-color: #f1f8e9; padding: 10px; margin: 15px 0; border-radius: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #2e7d32; color: white; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>📖 کارتی نمرەی قوتابی - بنکەی قورئان</h1></div>
        <div class="info-box">
            <p><strong>ناوی قوتابی:</strong> {student_info['full_name']} | <strong>کۆد:</strong> {student_info['student_code']}</p>
            <p><strong>پۆل:</strong> {student_info['class_num']} | <strong>ئاست:</strong> {student_info['level_type']}</p>
        </div>
        <table>
            <thead><tr><th>بابەت</th><th>وەرز</th><th>ڕۆژانە</th><th>تاقیکردنەوە</th><th>کۆی نمرە</th></tr></thead>
            <tbody>{rows_html if rows_html else '<tr><td colspan="5">هیچ نمرەیەک نییە</td></tr>'}</tbody>
        </table>
    </body>
    </html>
    """
    return HTML(string=html_content).write_pdf()

# 4. دەستەی بەڕێوەبەر (Admin)
def admin_dashboard():
    st.title(f"👑 بەخێربێیت بەڕێوەبەر")
    if st.button("دەرچوون (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    menu = [
        "تۆمارکردنی یەک قوتابی", 
        "تۆمارکردنی بەکۆمەڵی قوتابیان (Paste)",
        "تۆمارکردنی مامۆستا و دیاریکردنی پۆل", 
        "دەستکاریکردنی نمرەی قوتابیان", 
        "تۆمارکردنی نمرەی مامۆستا", 
        "پرێنتکردنی کارتی قوتابی", 
        "گۆڕینی وشەی نهێنی"
    ]
    choice = st.sidebar.selectbox("بەشەکان", menu)
    
    conn = get_db_connection()
    c = conn.cursor()

    if choice == "تۆمارکردنی یەک قوتابی":
        st.subheader("👨‍🎓 تۆمارکردنی قوتابی بە تەنها")
        code = st.text_input("کۆدی قوتابی")
        name = st.text_input("ناوی تەواوی قوتابی")
        cls = st.number_input("ژمارەی پۆل (1 تا 12)", min_value=1, max_value=12, step=1)
        level_type = st.selectbox("ئاستی خوێندن", ["خوێندنی ئاسایی (1-6)", "لەبەرکردنی قورئان (7-12)"])
        level = "teaching" if "1-6" in level_type else "hifz"
        addr = st.text_input("شوێنی دانیشتن")
        phone = st.text_input("ژمارەی مۆبایل")

        if st.button("تۆمارکردن"):
            if code and name:
                try:
                    c.execute("INSERT INTO students VALUES (?,?,?,?,?,?)", (code, name, level, int(cls), addr, phone))
                    conn.commit()
                    st.success("قوتابی تۆمارکرا!")
                except Exception as e:
                    st.error("کۆدەکە دووبارەیە یان هەڵەیەک هەیە.")
            else:
                st.warning("کۆد و ناو پڕبکەرەوە.")

    elif choice == "تۆمارکردنی بەکۆمەڵی قوتابیان (Paste)":
        st.subheader("📋 تۆمارکردنی ناوەکان بەکۆمەڵ")
        st.info("دەتوانیت لیستێک لە ناوی قوتابیان پەیست بکەیت؛ هەر ناوێک لە دێڕێکدا بنووسە.")
        
        cls_bulk = st.number_input("پۆلی سەرجەم ئەم قوتابیانە", min_value=1, max_value=12, step=1)
        start_code = st.number_input("کۆدی سەرەتایی (بۆ نموونە 101 بۆ قوتابی یەکەم)", min_value=1, value=100)
        level_type_bulk = st.selectbox("ئاستی خوێندن بۆ هەموویان", ["خوێندنی ئاسایی (1-6)", "لەبەرکردنی قورئان (7-12)"])
        level_b = "teaching" if "1-6" in level_type_bulk else "hifz"
        
        raw_names = st.text_area("لیستی ناوی قوتابیان لێرە پەیست بکه (کۆپی لە Excel یان Text):", height=200)

        if st.button("تۆمارکردنی هەموو ناوان بەکۆمەڵ"):
            names_list = [n.strip() for n in raw_names.split("\n") if n.strip()]
            if names_list:
                added_count = 0
                current_code = start_code
                for st_name in names_list:
                    try:
                        c.execute("INSERT INTO students VALUES (?,?,?,?,?,?)", (str(current_code), st_name, level_b, int(cls_bulk), "", ""))
                        added_count += 1
                        current_code += 1
                    except:
                        current_code += 1 # پەڕاندن لە کاتی هەبوونی کۆدی دووبارە
                conn.commit()
                st.success(f"بە سەرکەوتوویی ({added_count}) قوتابی تۆمارکران!")
            else:
                st.warning("تکایە هەندێک ناو لە چوارچێوەکە بنووسە یان پەیست بکە.")

    elif choice == "تۆمارکردنی مامۆستا و دیاریکردنی پۆل":
        st.subheader("👨‍🏫 تۆمارکردنی مامۆستا")
        code = st.text_input("کۆدی مامۆستا")
        name = st.text_input("ناوی تەواوی مامۆستا")
        uname = st.text_input("ناوی بەکارهێنەر")
        pwd = st.text_input("وشەی نهێنی", type="password")
        classes = st.text_input("پۆلە سپێردراوەکان (نموونە: 1, 2, 3)")
        
        if st.button("زیادکردنی مامۆستا"):
            try:
                c.execute("INSERT INTO teachers (teacher_code, full_name, username, password, assigned_classes) VALUES (?,?,?,?,?)",
                          (code, name, uname, pwd, classes))
                conn.commit()
                st.success("مامۆستا زیادکرا!")
            except Exception as e:
                st.error("هەڵەیەک هەیە، ناوی بەکارهێنەر دووبارەیە.")

    elif choice == "دەستکاریکردنی نمرەی قوتابیان":
        st.subheader("📝 دەستکاریکردنی نمرەکان")
        c.execute("SELECT student_code, full_name, class_num FROM students")
        students_list = {f"{row['full_name']} (پۆلی {row['class_num']}) - کۆد: {row['student_code']}": row['student_code'] for row in c.fetchall()}
        
        if students_list:
            selected_student = st.selectbox("قوتابی هەڵبژێرە", list(students_list.keys()))
            st_code = students_list[selected_student]

            subject = st.text_input("ناوی بابەت / سوورەت")
            term = st.selectbox("وەرز", [1, 2])
            daily = st.number_input("نمرەی ڕۆژانە", min_value=0.0, max_value=50.0)
            exam = st.number_input("نمرەی تاقیکردنەوە", min_value=0.0, max_value=50.0)
            
            if st.button("تۆمارکردنی نمرە"):
                c.execute("INSERT INTO grades (student_code, subject_name, term, daily_score, exam_score) VALUES (?,?,?,?,?)",
                          (st_code, subject, term, daily, exam))
                conn.commit()
                st.success("نمرە تۆمارکرا!")
                st.rerun()

    elif choice == "تۆمارکردنی نمرەی مامۆستا":
        st.subheader("📖 نمرەی لەبەرکردنی مامۆستا")
        c.execute("SELECT id, full_name FROM teachers")
        teachers_list = {row["full_name"]: row["id"] for row in c.fetchall()}
        if teachers_list:
            selected_teacher = st.selectbox("مامۆستا هەڵبژێرە", list(teachers_list.keys()))
            surah = st.text_input("سوورەت / جوزء")
            score = st.number_input("نمرەی ڕۆژانە (0 - 5)", min_value=0.0, max_value=5.0)
            date = st.date_input("ڕێکەوت")
            if st.button("تۆمارکردن"):
                c.execute("INSERT INTO teacher_hifz (teacher_id, surah_or_juz, daily_score, date) VALUES (?,?,?,?)",
                          (teachers_list[selected_teacher], surah, score, str(date)))
                conn.commit()
                st.success("تۆمارکرا!")

    elif choice == "پرێنتکردنی کارتی قوتابی":
        st.subheader("🖨️ پرێنت و داگرتنی PDF")
        c.execute("SELECT * FROM students")
        students = c.fetchall()
        if students:
            st_dict = {f"{s['full_name']} (پۆلی {s['class_num']})": s for s in students}
            selected_st_name = st.selectbox("قوتابی هەڵبژێرە", list(st_dict.keys()))
            st_data = st_dict[selected_st_name]
            c.execute("SELECT * FROM grades WHERE student_code=?", (st_data['student_code'],))
            st_grades = c.fetchall()

            pdf_data = generate_student_card_pdf(st_data, st_grades)
            st.download_button("📥 داگرتنی کارتی قوتابی (PDF)", data=pdf_data, file_name=f"card_{st_data['student_code']}.pdf", mime="application/pdf")

    elif choice == "گۆڕینی وشەی نهێنی":
        change_password_section()

    conn.close()

# 5. دەستەی مامۆستا
def teacher_dashboard():
    teacher_info = st.session_state.user_info
    st.title(f"👨‍🏫 مامۆستا: {teacher_info['full_name']}")
    if st.button("دەرچوون (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    assigned_classes = [c.strip() for c in teacher_info['assigned_classes'].split(",") if c.strip()]
    st.info(f"پۆلەکانت: {', '.join(assigned_classes)}")

    menu = ["تۆمارکردنی نمرەی قوتابیانی پۆلەکەم", "بینینی نمرەکانی خۆم", "گۆڕینی وشەی نهێنی"]
    choice = st.sidebar.selectbox("بەشەکان", menu)
    conn = get_db_connection()
    c = conn.cursor()

    if choice == "تۆمارکردنی نمرەی قوتابیانی پۆلەکەم":
        if assigned_classes:
            placeholders = ','.join('?' * len(assigned_classes))
            c.execute(f"SELECT student_code, full_name, class_num FROM students WHERE class_num IN ({placeholders})", assigned_classes)
            students_list = {f"{row['full_name']} (پۆلی {row['class_num']})": row['student_code'] for row in c.fetchall()}
            
            if students_list:
                selected_student = st.selectbox("قوتابی هەڵبژێرە", list(students_list.keys()))
                subject = st.text_input("ناوی بابەت / سوورەت")
                term = st.selectbox("وەرز", [1, 2])
                daily = st.number_input("نمرەی ڕۆژانە", min_value=0.0, max_value=50.0)
                exam = st.number_input("نمرەی تاقیکردنەوە", min_value=0.0, max_value=50.0)
                
                if st.button("تۆمارکردنی نمرە"):
                    st_code = students_list[selected_student]
                    c.execute("INSERT INTO grades (student_code, subject_name, term, daily_score, exam_score) VALUES (?,?,?,?,?)",
                              (st_code, subject, term, daily, exam))
                    conn.commit()
                    st.success("نمرەکە تۆمارکرا!")
            else:
                st.info("هیچ قوتابییەک نییە.")

    elif choice == "بینینی نمرەکانی خۆم":
        df_my_scores = pd.read_sql_query("SELECT surah_or_juz as 'سوورەت', daily_score as 'نمرە', date as 'ڕێکەوت' FROM teacher_hifz WHERE teacher_id=?", conn, params=(teacher_info['id'],))
        st.dataframe(df_my_scores, use_container_width=True)

    elif choice == "گۆڕینی وشەی نهێنی":
        change_password_section()

    conn.close()

# 6. ڕاڕەوی سەرەکی
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Admin":
        admin_dashboard()
    else:
        teacher_dashboard()
