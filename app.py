import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

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
                    
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    student_code TEXT PRIMARY KEY, 
                    full_name TEXT, 
                    level_type TEXT, 
                    class_num INTEGER, 
                    address TEXT, 
                    phone TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS student_subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_code TEXT,
                    subject_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS custom_subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_name TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS daily_marks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_code TEXT,
                    subject_name TEXT,
                    term INTEGER,
                    mark REAL,
                    date TEXT)''')

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
    
    default_subjects = [
        "قورئان", "فەرموودە 1", "پەروەردە 1", "قاعدة النورانية", 
        "فقه", "لەبەرکردنی قورئان", "پێداچوونەوەی قورئان", 
        "فەرموودە 2", "پەروەردە 2", "تجوید"
    ]
    for sub in default_subjects:
        c.execute("INSERT OR IGNORE INTO custom_subjects (subject_name) VALUES (?)", (sub,))

    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO admins (username, password, full_name) VALUES ('admin', 'admin123', 'بەڕێوەبەری سەرەکی')")
    conn.commit()
    conn.close()

init_db()

def get_all_subjects():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT subject_name FROM custom_subjects")
    subs = [row['subject_name'] for row in c.fetchall()]
    conn.close()
    return subs

# 2. دیزاینی مۆدێرن و نەرم (Modern & Clean UI)
st.set_page_config(page_title="سیستەمی بنکەی قورئان", layout="wide", page_icon="📖")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"], div, input, label, select, textarea {
        direction: RTL !important;
        text-align: right !important;
        font-family: 'Vazirmatn', sans-serif !important;
    }
    
    .stApp {
        background-color: #f8fafc !important;
    }
    
    /* کارتە ئامارییەکان */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-title {
        color: #64748b;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #0f172a;
        font-size: 28px;
        font-weight: 700;
    }

    /* دوگمەکان */
    .stButton>button {
        background-color: #10b981 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #059669 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
    }

    /* فۆرمەکان و خشتەکان */
    input, select, textarea, [data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
    }
    
    .card-box {
        border: 1px solid #e2e8f0;
        padding: 25px;
        border-radius: 16px;
        background-color: #ffffff;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_info = None

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
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;'>
                <h2 style='color: #0f172a; margin-bottom: 5px;'>📖 سیستەمی بنکەی قورئان</h2>
                <p style='color: #64748b; font-size: 14px;'>تکایە زانیارییەکانت بنووسە بۆ چوونەژوورەوە</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("ناوی بەکارهێنەر")
            password = st.text_input("وشەی نهێنی", type="password")
            submit = st.form_submit_button("چوونەژوورەوە", use_container_width=True)
            
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

                c.execute("SELECT * FROM teachers WHERE username=? AND password=?", (username, password))
                teacher = c.fetchone()
                conn.close()
                
                if teacher:
                    st.session_state.logged_in = True
                    st.session_state.role = "Teacher"
                    st.session_state.user_info = dict(teacher)
                    st.rerun()
                
                st.error("ناوی بەکارهێنەر یان وشەی نهێنی هەڵەیە!")

# 4. دەستەی بەڕێوەبەر (Admin Dashboard)
def admin_dashboard():
    st.markdown(f"<h2 style='color: #0f172a;'>👑 هەژماری بەڕێوەبەرایەتی</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    c = conn.cursor()

    # هەژمارکردنی ئامارە گشتییەکان
    c.execute("SELECT COUNT(*) FROM students")
    total_students = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM teachers")
    total_teachers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM custom_subjects")
    total_subs = c.fetchone()[0]

    # کارتەکانی ئامار
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.markdown(f"<div class='metric-card'><div class='metric-title'>تێکڕای قوتابیان</div><div class='metric-value'>{total_students}</div></div>", unsafe_allow_html=True)
    col_m2.markdown(f"<div class='metric-card'><div class='metric-title'>تێکڕای مامۆستایان</div><div class='metric-value'>{total_teachers}</div></div>", unsafe_allow_html=True)
    col_m3.markdown(f"<div class='metric-card'><div class='metric-title'>وانە بەردەستەکان</div><div class='metric-value'>{total_subs}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    menu = [
        "📊 داشبۆردی گشتی و گەڕان",
        "📂 قوتابیان بەپێی ژوورەکان (1-20)",
        "➕ تۆمارکردنی یەک قوتابی", 
        "📋 تۆمارکردنی بەکۆمەڵ (Paste)",
        "🎯 دیاریکردنی وانەکانی قوتابی",
        "⚙️ بەڕێوەبردنی وانەکان",
        "👨‍🏫 تۆمارکردنی مامۆستا", 
        "📅 غیابات و هاتوو",
        "📝 نمرەی تاقیکردنەوە (30)", 
        "📄 کارتی A4 و ڕاپۆرت"
    ]
    
    st.sidebar.title("بەشەکانی سیستەم")
    choice = st.sidebar.radio("هەڵبژاردن:", menu)
    
    if st.sidebar.button("🚪 دەرچوون (Logout)", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    if choice == "📊 داشبۆردی گشتی و گەڕان":
        st.subheader("🔍 گەڕانی خێرا و بینینی زانیاری قوتابی")
        search_query = st.text_input("ناوی قوتابی یان کۆد بنووسە:")
        
        if search_query:
            c.execute("SELECT * FROM students WHERE full_name LIKE ? OR student_code LIKE ?", (f"%{search_query}%", f"%{search_query}%"))
            results = c.fetchall()
            
            if results:
                for st_data in results:
                    with st.expander(f"👤 {st_data['full_name']} | ژووری ({st_data['class_num']}) | کۆد: {st_data['student_code']}"):
                        c1, c2 = st.columns(2)
                        c1.write(f"**ناوی تەواو:** {st_data['full_name']}")
                        c1.write(f"**کۆد:** {st_data['student_code']}")
                        c2.write(f"**ژوور/پۆل:** {st_data['class_num']}")
                        c2.write(f"**مۆبایل:** {st_data['phone'] if st_data['phone'] else 'دیاری نەکراوە'}")
                        
                        df_grades = get_student_grades_df(st_data['student_code'], conn)
                        st.dataframe(df_grades, use_container_width=True)
            else:
                st.warning("هیچ ئەنجامێک نەدۆزرایەوە.")

    elif choice == "📂 قوتابیان بەپێی ژوورەکان (1-20)":
        st.subheader("🏢 شیت و لیستی قوتابیان بەپێی ژوور")
        selected_room = st.selectbox("ژوور هەڵبژێرە:", list(range(1, 21)))
        
        c.execute("SELECT student_code as 'کۆد', full_name as 'ناوی تەواو', phone as 'مۆبایل' FROM students WHERE class_num=?", (selected_room,))
        room_students = c.fetchall()
        
        if room_students:
            st.dataframe(pd.DataFrame(room_students), use_container_width=True)
        else:
            st.info("ئەم ژوورە بەتاڵە.")

    elif choice == "➕ تۆمارکردنی یەک قوتابی":
        st.subheader("➕ تۆمارکردنی قوتابیی نوێ")
        c1, c2 = st.columns(2)
        code = c1.text_input("کۆدی قوتابی")
        name = c2.text_input("ناوی تەواو")
        cls = c1.number_input("ژوور (1 تا 20)", min_value=1, max_value=20, step=1)
        phone = c2.text_input("ژمارەی مۆبایل")

        all_subs = get_all_subjects()
        selected_subs = st.multiselect("وانەکانی قوتابی (1 تا 3 وانە)", all_subs, max_selections=3)

        if st.button("پاشەکەوتکردن"):
            if code and name:
                c.execute("INSERT INTO students VALUES (?,?,?,?,?,?)", (code, name, "", int(cls), "", phone))
                for sub in selected_subs:
                    c.execute("INSERT INTO student_subjects (student_code, subject_name) VALUES (?,?)", (code, sub))
                conn.commit()
                st.success("تۆمارکرا!")

    elif choice == "📋 تۆمارکردنی بەکۆمەڵ (Paste)":
        st.subheader("📋 تۆمارکردنی بەکۆمەڵ")
        cls_bulk = st.number_input("ژوور (1 تا 20)", min_value=1, max_value=20, step=1)
        start_code = st.number_input("کۆدی دەستپێک", min_value=1, value=100)
        raw_names = st.text_area("لیستی ناوەکان پەیست بکه:", height=150)

        if st.button("تۆمارکردنی هەموویان"):
            names_list = [n.strip() for n in raw_names.split("\n") if n.strip()]
            cur = start_code
            for st_name in names_list:
                try:
                    c.execute("INSERT INTO students VALUES (?,?,?,?,?,?)", (str(cur), st_name, "", int(cls_bulk), "", ""))
                    cur += 1
                except:
                    cur += 1
            conn.commit()
            st.success("ناوەکان تۆمارکران!")

    elif choice == "🎯 دیاریکردنی وانەکانی قوتابی":
        st.subheader("🎯 دیاریکردنی وانەکانی قوتابی")
        c.execute("SELECT student_code, full_name, class_num FROM students")
        st_dict = {f"{r['full_name']} (ژووری {r['class_num']})": r['student_code'] for r in c.fetchall()}
        
        if st_dict:
            s_name = st.selectbox("قوتابی هەڵبژێرە", list(st_dict.keys()))
            st_code = st_dict[s_name]
            all_subs = get_all_subjects()
            
            c.execute("SELECT subject_name FROM student_subjects WHERE student_code=?", (st_code,))
            curr_subs = [r['subject_name'] for r in c.fetchall()]
            
            new_subs = st.multiselect("وانەکان (زۆرترین 3 وانە):", all_subs, default=curr_subs, max_selections=3)
            if st.button("نوێکردنەوە"):
                c.execute("DELETE FROM student_subjects WHERE student_code=?", (st_code,))
                for sub in new_subs:
                    c.execute("INSERT INTO student_subjects (student_code, subject_name) VALUES (?,?)", (st_code, sub))
                conn.commit()
                st.success("نوێکرایەوە!")

    elif choice == "⚙️ بەڕێوەبردنی وانەکان":
        st.subheader("⚙️ بەڕێوەبردنی وانەکان")
        all_subs = get_all_subjects()
        st.write("**وانە چالاکەکان:** ", ", ".join(all_subs))
        
        c1, c2 = st.columns(2)
        new_s = c1.text_input("وانەی نوێ:")
        if c1.button("زیادکردن"):
            c.execute("INSERT OR IGNORE INTO custom_subjects (subject_name) VALUES (?)", (new_s,))
            conn.commit()
            st.rerun()

        del_s = c2.selectbox("وانە بۆ سڕینەوە:", all_subs)
        if c2.button("سڕینەوە"):
            c.execute("DELETE FROM custom_subjects WHERE subject_name=?", (del_s,))
            conn.commit()
            st.rerun()

    elif choice == "👨‍🏫 تۆمارکردنی مامۆستا":
        st.subheader("👨‍🏫 تۆمارکردنی مامۆستا")
        c1, c2 = st.columns(2)
        code = c1.text_input("کۆد")
        name = c2.text_input("ناوی تەواو")
        uname = c1.text_input("ناوی بەکارهێنەر")
        pwd = c2.text_input("وشەی نهێنی", type="password")

        all_subs = get_all_subjects()
        cls1 = c1.number_input("ژووری یەکەم", min_value=1, max_value=20)
        sub1 = c1.selectbox("وانەی یەکەم", all_subs, key="m_sub1")
        
        cls2 = c2.number_input("ژووری دووەم", min_value=1, max_value=20)
        sub2 = c2.selectbox("وانەی دووەم", all_subs, key="m_sub2")

        if st.button("زیادکردنی مامۆستا"):
            sub_str = f"{cls1}:{sub1}|{cls2}:{sub2}"
            c.execute("INSERT INTO teachers (teacher_code, full_name, username, password, assigned_classes, assigned_subjects) VALUES (?,?,?,?,?,?)",
                      (code, name, uname, pwd, f"{cls1},{cls2}", sub_str))
            conn.commit()
            st.success("مامۆستا تۆمارکرا!")

    elif choice == "📅 غیابات و هاتوو":
        st.subheader("📅 ئامادەبوونی ڕۆژانە")
        selected_cls = st.number_input("ژوور (1-20)", min_value=1, max_value=20)
        att_date = st.date_input("ڕێکەوت (ئۆتۆماتیک)", datetime.now())
        
        c.execute("SELECT student_code, full_name FROM students WHERE class_num=?", (selected_cls,))
        st_list = c.fetchall()
        
        if st_list:
            att_map = {}
            for row in st_list:
                col_a, col_b = st.columns([2, 2])
                col_a.write(f"👤 {row['full_name']}")
                att_map[row['student_code']] = col_b.radio("دۆخ", ["هاتوو", "مۆڵەت", "نەهاتوو"], key=f"rad_{row['student_code']}", horizontal=True)
            
            if st.button("پاشەکەوتکردن"):
                for scode, sstat in att_map.items():
                    c.execute("INSERT INTO attendance (student_code, date, status) VALUES (?,?,?)", (scode, str(att_date), sstat))
                conn.commit()
                st.success("تۆمارکرا!")

    elif choice == "📝 نمرەی تاقیکردنەوە (30)":
        st.subheader("📝 نمرەی تاقیکردنەوە (30)")
        c.execute("SELECT student_code, full_name FROM students")
        st_map = {f"{r['full_name']} ({r['student_code']})": r['student_code'] for r in c.fetchall()}
        
        if st_map:
            s_select = st.selectbox("قوتابی", list(st_map.keys()))
            scode = st_map[s_select]
            sub = st.selectbox("وانە", get_all_subjects())
            term = st.selectbox("وەرز", [1, 2])
            score = st.number_input("نمرە (0-30)", min_value=0.0, max_value=30.0, step=0.5)
            
            if st.button("پاشەکەوت"):
                c.execute("INSERT OR REPLACE INTO exam_marks (student_code, subject_name, term, exam_score) VALUES (?,?,?,?)",
                          (scode, sub, term, score))
                conn.commit()
                st.success("نمرە تۆمارکرا!")

    elif choice == "📄 کارتی A4 و ڕاپۆرت":
        st.subheader("📄 کارتی ڕاپۆرتی قوتابی")
        c.execute("SELECT * FROM students")
        st_rows = c.fetchall()
        if st_rows:
            st_dict = {f"{s['full_name']} (ژووری {s['class_num']})": s for s in st_rows}
            s_choice = st.selectbox("قوتابی هەڵبژێرە", list(st_dict.keys()))
            s_data = st_dict[s_choice]
            
            df_g = get_student_grades_df(s_data['student_code'], conn)
            
            st.markdown(f"""
            <div class="card-box">
                <h3 style="text-align: center; color: #10b981;">📖 سیستەمی بنکەی قورئان - کارتی نمرە</h3>
                <hr>
                <p><b>ناوی قوتابی:</b> {s_data['full_name']} | <b>کۆد:</b> {s_data['student_code']} | <b>ژوور:</b> {s_data['class_num']}</p>
                <hr>
            </div>
            """, unsafe_allow_html=True)
            st.dataframe(df_g, use_container_width=True)

    conn.close()

# 5. دەستەی مامۆستا (Teacher Dashboard)
def teacher_dashboard():
    t_info = st.session_state.user_info
    st.markdown(f"<h2>👨‍🏫 بەخێربێیت مامۆستا {t_info['full_name']}</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 دەرچوون", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    raw_subs = t_info.get('assigned_subjects', '')
    parsed = []
    if raw_subs:
        for item in raw_subs.split('|'):
            if ':' in item:
                c_str, s_str = item.split(':')
                parsed.append((c_str.strip(), s_str.strip()))

    st.subheader("✏️ تۆمارکردنی نمرەی ڕۆژانەی قوتابیان")
    if parsed:
        opts = [f"ژووری {c_num} - وانەی: {s_num}" for c_num, s_num in parsed]
        sel = st.selectbox("ژوور و وانە:", opts)
        idx = opts.index(sel)
        target_cls, target_sub = parsed[idx]
        
        m_date = st.date_input("ڕێکەوت (ئۆتۆماتیک)", datetime.now())
        term = st.selectbox("وەرز", [1, 2])

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT student_code, full_name FROM students WHERE class_num=?", (target_cls,))
        st_in_cls = c.fetchall()

        if st_in_cls:
            marks = {}
            for r in st_in_cls:
                c1, c2 = st.columns([2, 2])
                c1.write(f"👤 **{r['full_name']}**")
                marks[r['student_code']] = c2.number_input("نمرەی ئەمڕۆ", min_value=0.0, max_value=20.0, step=0.5, key=f"tm_{r['student_code']}")
            
            if st.button("پاشەکەوتکردن"):
                for scode, smark in marks.items():
                    c.execute("INSERT INTO daily_marks (student_code, subject_name, term, mark, date) VALUES (?,?,?,?,?)",
                              (scode, target_sub, term, smark, str(m_date)))
                conn.commit()
                st.success("نمرەکان پاشەکەوت بڕان!")
        conn.close()

# 6. ڕاڕەوی سەرەکی
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Admin":
        admin_dashboard()
    else:
        teacher_dashboard()
