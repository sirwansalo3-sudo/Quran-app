import streamlit as st
import sqlite3
import pandas as pd

# 1. بنکەی دراوە (Database Setup)
def get_db_connection():
    conn = sqlite3.connect('quran_center_web.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, full_name TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    teacher_code TEXT UNIQUE, 
                    full_name TEXT, 
                    username TEXT UNIQUE, 
                    password TEXT, 
                    assigned_classes TEXT,
                    assigned_subjects TEXT)''')
                    
    c.execute('''CREATE TABLE IF NOT EXISTS students (student_code TEXT PRIMARY KEY, full_name TEXT, level_type TEXT, class_num INTEGER, address TEXT, phone TEXT)''')
    
    # خشتەی تۆمارکردنی نمرەی ڕۆژانە
    c.execute('''CREATE TABLE IF NOT EXISTS daily_marks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_code TEXT,
                    subject_name TEXT,
                    term INTEGER,
                    mark REAL,
                    date TEXT)''')

    # خشتەی نمرەی تاقیکردنەوەکان
    c.execute('''CREATE TABLE IF NOT EXISTS exam_marks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_code TEXT,
                    subject_name TEXT,
                    term INTEGER,
                    exam_score REAL,
                    UNIQUE(student_code, subject_name, term))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS teacher_hifz (id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_id INTEGER, surah_or_juz TEXT, daily_score REAL, date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_code TEXT,
                    date TEXT,
                    status TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO admins (username, password, full_name) VALUES ('admin', 'admin123', 'بەڕێوەبەری سەرەکی')")
    conn.commit()
    conn.close()

init_db()

# 2. ڕێکخستنی دیزاین (CSS)
st.set_page_config(page_title="سیستەمی بنکەی قورئان", layout="wide")

st.markdown("""
    <style>
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
    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    @media print {
        body * {
            visibility: hidden;
        }
        #a4-card, #a4-card * {
            visibility: visible;
        }
        #a4-card {
            position: absolute;
            left: 0;
            top: 0;
            width: 210mm;
            height: 297mm;
            padding: 15mm;
            box-sizing: border-box;
            background-color: white;
        }
        .no-print {
            display: none !important;
        }
    }

    .card-box {
        border: 2px solid #2e7d32;
        padding: 25px;
        border-radius: 12px;
        background-color: #fafafa;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_info = None

SUBJECTS_LIST = ["لەبەرکردنی قوران", "پێداچوونەوەی قوران", "فەرموودە 2", "پەروەردە 2", "تەجوید"]

# هەژمارکردنی نمرەکان
def get_student_grades_df(student_code, conn):
    query = """
        SELECT 
            d.subject_name AS 'وانە / بابەت',
            d.term AS 'وەرز',
            ROUND(MIN(20.0, IFNULL(SUM(d.mark), 0)), 2) AS 'کۆی ڕۆژانە (20)',
            IFNULL(e.exam_score, 0) AS 'تاقیکردنەوە (30)',
            ROUND(MIN(20.0, IFNULL(SUM(d.mark), 0)) + IFNULL(e.exam_score, 0), 2) AS 'کۆی گشتی (50)'
        FROM daily_marks d
        LEFT JOIN exam_marks e 
            ON d.student_code = e.student_code 
            AND d.subject_name = e.subject_name 
            AND d.term = e.term
        WHERE d.student_code = ?
        GROUP BY d.subject_name, d.term
    """
    return pd.read_sql_query(query, conn, params=(student_code,))

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

# 4. دەستەی بەڕێوەبەر (Admin Dashboard)
def admin_dashboard():
    st.title(f"👑 بەخێربێیت بەڕێوەبەر")
    if st.button("دەرچوون (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    menu = [
        "🔍 گەڕان بەدوای قوتابی",
        "تۆمارکردنی یەک قوتابی", 
        "تۆمارکردنی بەکۆمەڵی قوتابیان (Paste)",
        "تۆمارکردنی مامۆستا و وانەکانی", 
        "تۆمارکردنی غیابات و هاتوو",
        "تۆمارکردنی نمرەی تاقیکردنەوە (30)", 
        "تۆمارکردنی نمرەی مامۆستا", 
        "کارتی نمرەی A4 و ڕاپۆرتی غیابات", 
        "گۆڕینی وشەی نهێنی"
    ]
    choice = st.sidebar.selectbox("بەشەکان", menu)
    
    conn = get_db_connection()
    c = conn.cursor()

    if choice == "🔍 گەڕان بەدوای قوتابی":
        st.subheader("🔍 گەڕانی خێرا بۆ ناوی قوتابی")
        search_query = st.text_input("ناوی قوتابی یان کۆدەکەی بنووسە بۆ گەڕان:")
        
        if search_query:
            c.execute("SELECT * FROM students WHERE full_name LIKE ? OR student_code LIKE ?", (f"%{search_query}%", f"%{search_query}%"))
            results = c.fetchall()
            
            if results:
                st.success(f"ژمارەی دۆزراوەکان: {len(results)}")
                for st_data in results:
                    with st.expander(f"👤 {st_data['full_name']} (پۆلی {st_data['class_num']}) - کۆد: {st_data['student_code']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**کۆدی قوتابی:** {st_data['student_code']}")
                            st.write(f"**ناوی تەواو:** {st_data['full_name']}")
                            st.write(f"**پۆل:** {st_data['class_num']}")
                        with col2:
                            st.write(f"**ئاستی خوێندن:** {'خوێندنی ئاسایی' if st_data['level_type'] == 'teaching' else 'لەبەرکردنی قورئان'}")
                            st.write(f"**شوێنی دانیشتن:** {st_data['address'] if st_data['address'] else 'تۆمار نەکراوە'}")
                            st.write(f"**ژمارەی مۆبایل:** {st_data['phone'] if st_data['phone'] else 'تۆمار نەکراوە'}")
                        
                        st.markdown("---")
                        
                        c.execute("SELECT status, COUNT(*) as count FROM attendance WHERE student_code=? GROUP BY status", (st_data['student_code'],))
                        att_summary = {row['status']: row['count'] for row in c.fetchall()}
                        
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("ڕۆژانی هاتوو", att_summary.get('هاتوو', 0))
                        col_b.metric("ڕۆژانی مۆڵەت", att_summary.get('مۆڵەت', 0))
                        col_c.metric("ڕۆژانی نەهاتوو (غیاب)", att_summary.get('نەهاتوو', 0))
                        
                        st.markdown("---")
                        st.write("📊 **خشتەی نمرەکانی قوتابی:**")
                        df_grades = get_student_grades_df(st_data['student_code'], conn)
                        if not df_grades.empty:
                            st.dataframe(df_grades, use_container_width=True)
                        else:
                            st.info("هیچ نمرەیەک بۆ ئەم قوتابییە تۆمار نەکراوە.")
            else:
                st.warning("هیچ قوتابییەک بەم ناوە یان کۆدە نەدۆزرایەوە.")

    elif choice == "تۆمارکردنی یەک قوتابی":
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

    elif choice == "تۆمارکردنی بەکۆمەڵی قوتابیان (Paste)":
        st.subheader("📋 تۆمارکردنی ناوەکان بەکۆمەڵ")
        cls_bulk = st.number_input("پۆلی سەرجەم ئەم قوتابیانە", min_value=1, max_value=12, step=1)
        start_code = st.number_input("کۆدی سەرەتایی (بۆ نموونە 101 بۆ قوتابی یەکەم)", min_value=1, value=100)
        level_type_bulk = st.selectbox("ئاستی خوێندن بۆ هەموویان", ["خوێندنی ئاسایی (1-6)", "لەبەرکردنی قورئان (7-12)"])
        level_b = "teaching" if "1-6" in level_type_bulk else "hifz"
        
        raw_names = st.text_area("لیستی ناوی قوتابیان لێرە پەیست بکه:", height=200)

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
                        current_code += 1
                conn.commit()
                st.success(f"بە سەرکەوتوویی ({added_count}) قوتابی تۆمارکران!")

    elif choice == "تۆمارکردنی مامۆستا و وانەکانی":
        st.subheader("👨‍🏫 تۆمارکردنی مامۆستای ئاستی فێرکردن")
        code = st.text_input("کۆدی مامۆستا")
        name = st.text_input("ناوی تەواوی مامۆستا")
        uname = st.text_input("ناوی بەکارهێنەر (Username)")
        pwd = st.text_input("وشەی نهێنی (Password)", type="password")
        
        st.markdown("---")
        st.markdown("### 📚 هەڵبژاردنی ۳ وانە و پۆلەکانی مامۆستا")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**پۆلی یەکەم:**")
            class1 = st.number_input("ژمارەی پۆلی یەکەم", min_value=1, max_value=12, step=1, key="c1")
            sub1_1 = st.selectbox("وانەی یەکەمی پۆلی یەکەم", SUBJECTS_LIST, key="s1_1")
            sub1_2 = st.selectbox("وانەی دووەمی پۆلی یەکەم", [s for s in SUBJECTS_LIST if s != sub1_1], key="s1_2")
            
        with col2:
            st.write("**پۆلی دووەم:**")
            class2 = st.number_input("ژمارەی پۆلی دووەم", min_value=1, max_value=12, step=1, key="c2")
            used_subs = [sub1_1, sub1_2]
            sub2_1 = st.selectbox("وانەی سێیەم (لە پۆلی دووەم)", [s for s in SUBJECTS_LIST if s not in used_subs], key="s2_1")

        if st.button("زیادکردنی مامۆستا"):
            if uname and pwd and name:
                classes_str = f"{class1},{class2}"
                subjects_str = f"{class1}:{sub1_1}|{class1}:{sub1_2}|{class2}:{sub2_1}"
                try:
                    c.execute("INSERT INTO teachers (teacher_code, full_name, username, password, assigned_classes, assigned_subjects) VALUES (?,?,?,?,?,?)",
                              (code, name, uname, pwd, classes_str, subjects_str))
                    conn.commit()
                    st.success("مامۆستا بە سەركەوتوویی لەگەڵ ۳ وانەکەی دیاریکرا!")
                except Exception as e:
                    st.error("کێشەیەک هەیە، ناوی بەکارهێنەر دووبارەیە.")

    elif choice == "تۆمارکردنی غیابات و هاتوو":
        st.subheader("📅 لیستی ئامادەبوون و غیاباتی ڕۆژانە")
        selected_cls = st.number_input("پۆلەکە دیاری بکە", min_value=1, max_value=12, step=1)
        att_date = st.date_input("ڕێکەوت")
        
        c.execute("SELECT student_code, full_name FROM students WHERE class_num=?", (selected_cls,))
        students_in_cls = c.fetchall()
        
        if students_in_cls:
            st.write(f"**تۆمارکردنی ئامادەبوونی پۆلی {selected_cls} بۆ ڕێکەوتی {att_date}:**")
            att_data = {}
            for st_row in students_in_cls:
                col_st1, col_st2 = st.columns([2, 2])
                with col_st1:
                    st.write(f"👤 {st_row['full_name']} ({st_row['student_code']})")
                with col_st2:
                    status = st.radio(f"باری ئامادەبوون", ["هاتوو", "مۆڵەت", "نەهاتوو"], key=f"att_{st_row['student_code']}", horizontal=True)
                    att_data[st_row['student_code']] = status
            
            if st.button("پاشەکەوتکردنی ئامادەبوون"):
                for s_code, s_status in att_data.items():
                    c.execute("INSERT INTO attendance (student_code, date, status) VALUES (?,?,?)", (s_code, str(att_date), s_status))
                conn.commit()
                st.success("ئامادەبوونی ڕۆژانە پاشەکەوت بڕا!")
        else:
            st.warning("هیچ قوتابییەک لەم پۆلەدا تۆمار نەکراوە.")

    elif choice == "تۆمارکردنی نمرەی تاقیکردنەوە (30)":
        st.subheader("📝 تۆمارکردنی نمرەی تاقیکردنەوەی سەرەکی (لەسەر 30)")
        c.execute("SELECT student_code, full_name, class_num FROM students")
        students_list = {f"{row['full_name']} (پۆلی {row['class_num']}) - کۆد: {row['student_code']}": row['student_code'] for row in c.fetchall()}
        
        if students_list:
            selected_student = st.selectbox("قوتابی هەڵبژێرە", list(students_list.keys()))
            st_code = students_list[selected_student]

            subject = st.selectbox("ناوی وانە / بابەت", SUBJECTS_LIST)
            term = st.selectbox("وەرز", [1, 2])
            exam_mark = st.number_input("نمرەی تاقیکردنەوە (0 تا 30)", min_value=0.0, max_value=30.0, step=0.5)
            
            if st.button("پاشەکەوتکردنی نمرەی تاقیکردنەوە"):
                c.execute("INSERT OR REPLACE INTO exam_marks (student_code, subject_name, term, exam_score) VALUES (?,?,?,?)",
                          (st_code, subject, term, exam_mark))
                conn.commit()
                st.success("نمرەی تاقیکردنەوە بە سەرکەوتوویی تۆمارکرا!")

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

    elif choice == "کارتی نمرەی A4 و ڕاپۆرتی غیابات":
        st.subheader("📄 کارتی ڕاپۆرتی قوتابی (ئامادەکراو بۆ A4)")
        c.execute("SELECT * FROM students")
        students = c.fetchall()
        if students:
            st_dict = {f"{s['full_name']} (پۆلی {s['class_num']})": s for s in students}
            selected_st_name = st.selectbox("قوتابی هەڵبژێرە", list(st_dict.keys()))
            st_data = st_dict[selected_st_name]
            
            c.execute("SELECT status, COUNT(*) as count FROM attendance WHERE student_code=? GROUP BY status", (st_data['student_code'],))
            att_summary = {row['status']: row['count'] for row in c.fetchall()}
            
            present_count = att_summary.get('هاتوو', 0)
            leave_count = att_summary.get('مۆڵەت', 0)
            absent_count = att_summary.get('نەهاتوو', 0)
            
            df_grades = get_student_grades_df(st_data['student_code'], conn)

            st.markdown(f"""
            <div id="a4-card" class="card-box">
                <h2 style="text-align: center; color: #2e7d32;">📖 سیستەمی بنکەی قورئان - کارتی نمرە و غیابات</h2>
                <hr>
                <div style="display: flex; justify-content: space-between; font-size: 16px;">
                    <p><b>ناوی قوتابی:</b> {st_data['full_name']}</p>
                    <p><b>کۆدی قوتابی:</b> {st_data['student_code']}</p>
                    <p><b>پۆل:</b> {st_data['class_num']}</p>
                </div>
                <hr>
                <h4>📊 کورتەی ئامادەبوون و غیابات:</h4>
                <ul>
                    <li><b>ڕۆژانی هاتوو:</b> {present_count} ڕۆژ</li>
                    <li><b>ڕۆژانی مۆڵەت:</b> {leave_count} ڕۆژ</li>
                    <li><b>ڕۆژانی نەهاتوو (غیاب):</b> {absent_count} ڕۆژ</li>
                </ul>
                <hr>
                <h4>📝 خشتی نمرەکانی قوتابی (وەرزی یەکەم / کۆ لەسەر 50):</h4>
            </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(df_grades, use_container_width=True)

    elif choice == "گۆڕینی وشەی نهێنی":
        change_password_section()

    conn.close()

# 5. دەستەی مامۆستا (Teacher Dashboard)
def teacher_dashboard():
    teacher_info = st.session_state.user_info
    st.title(f"👨‍🏫 مامۆستا: {teacher_info['full_name']}")
    if st.button("دەرچوون (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    raw_subjects = teacher_info.get('assigned_subjects', '')
    parsed_assignments = []
    if raw_subjects:
        for item in raw_subjects.split('|'):
            if ':' in item:
                cls_str, sub_str = item.split(':')
                parsed_assignments.append((cls_str.strip(), sub_str.strip()))

    menu = ["تۆمارکردنی نمرەی ڕۆژانەی قوتابیان", "تۆمارکردنی غیاباتی پۆلەکەم", "بینینی نمرەکانی خۆم", "گۆڕینی وشەی نهێنی"]
    choice = st.sidebar.selectbox("بەشەکان", menu)
    conn = get_db_connection()
    c = conn.cursor()

    if choice == "تۆمارکردنی نمرەی ڕۆژانەی قوتابیان":
        st.subheader("✏️ تۆمارکردنی نمرەی ڕۆژانەی قوتابیان")
        if parsed_assignments:
            options = [f"پۆلی {cls} - وانەی: {sub}" for cls, sub in parsed_assignments]
            selected_option = st.selectbox("پۆل و وانەکەت هەڵبژێرە", options)
            
            idx = options.index(selected_option)
            target_class, target_subject = parsed_assignments[idx]
            
            term = st.selectbox("وەرز", [1, 2])
            mark_date = st.date_input("ڕێکەوتی وانە")

            c.execute("SELECT student_code, full_name FROM students WHERE class_num=?", (target_class,))
            students_in_cls = c.fetchall()
            
            if students_in_cls:
                st.info(f"نمرەی ڕۆژانە بۆ پۆلی **{target_class}** - وانەی **{target_subject}** تۆمار دەکرێت:")
                marks_dict = {}
                for st_row in students_in_cls:
                    col1, col2 = st.columns([2, 2])
                    with col1:
                        st.write(f"👤 **{st_row['full_name']}** ({st_row['student_code']})")
                    with col2:
                        mark = st.number_input(f"نمرەی ئەمڕۆ", min_value=0.0, max_value=20.0, step=0.5, key=f"dmark_{st_row['student_code']}")
                        marks_dict[st_row['student_code']] = mark

                if st.button("پاشەکەوتکردنی نمرەی ڕۆژانە"):
                    for s_code, s_mark in marks_dict.items():
                        c.execute("INSERT INTO daily_marks (student_code, subject_name, term, mark, date) VALUES (?,?,?,?,?)",
                                  (s_code, target_subject, term, s_mark, str(mark_date)))
                    conn.commit()
                    st.success("نمرەی ڕۆژانەی هەموو قوتابیان بە سەرکەوتوویی پاشەکەوت بڕا!")
            else:
                st.warning(f"هیچ قوتابییەک لە پۆلی {target_class} تۆمار نەکراوە.")
        else:
            st.info("هیچ وانە و پۆلێک بۆ ئەم هەژمارە دیاری نەکراوە.")

    elif choice == "تۆمارکردنی غیاباتی پۆلەکەم":
        if parsed_assignments:
            classes_set = list(set([cls for cls, sub in parsed_assignments]))
            target_cls = st.selectbox("پۆلەکەت هەڵبژێرە", classes_set)
            att_date = st.date_input("ڕێکەوت")
            
            c.execute("SELECT student_code, full_name FROM students WHERE class_num=?", (target_cls,))
            students_in_cls = c.fetchall()
            
            if students_in_cls:
                att_data = {}
                for st_row in students_in_cls:
                    col_st1, col_st2 = st.columns([2, 2])
                    with col_st1:
                        st.write(f"👤 {st_row['full_name']}")
                    with col_st2:
                        status = st.radio(f"باری ئامادەبوون", ["هاتوو", "مۆڵەت", "نەهاتوو"], key=f"t_att_{st_row['student_code']}", horizontal=True)
                        att_data[st_row['student_code']] = status
                
                if st.button("پاشەکەوتکردنی غیابات"):
                    for s_code, s_status in att_data.items():
                        c.execute("INSERT INTO attendance (student_code, date, status) VALUES (?,?,?)", (s_code, str(att_date), s_status))
                    conn.commit()
                    st.success("ئامادەبوونەکە تۆمارکرا!")
        else:
            st.info("هیچ پۆلێک بۆ تۆ دیاری نەکراوە.")

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
