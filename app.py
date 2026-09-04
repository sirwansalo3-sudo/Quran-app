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
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_code TEXT,
                    date TEXT,
                    status TEXT,
                    notes TEXT)''')
    
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

# 2. دیزاینی مۆدێرن
st.set_page_config(page_title="سیستەمی بنکەی قورئان", layout="wide", page_icon="📖")

st.markdown("""
    <style>
    .stMainBlockContainer {
        direction: RTL;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, sans-serif;
    }
    .stApp { background-color: #f8fafc; }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-title { color: #64748b; font-size: 13px; font-weight: 600; }
    .metric-value { color: #0f172a; font-size: 24px; font-weight: 700; }
    .stButton>button {
        background-color: #10b981 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        width: 100%;
    }
    .card-box {
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
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
    st.title("📖 سیستەمی بنکەی قورئان")
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
    st.title("👑 هەژماری بەڕێوەبەری سەرەکی")
    
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM students")
    total_students = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM teachers")
    total_teachers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM custom_subjects")
    total_subs = c.fetchone()[0]

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.markdown(f"<div class='metric-card'><div class='metric-title'>تێکڕای قوتابیان</div><div class='metric-value'>{total_students}</div></div>", unsafe_allow_html=True)
    col_m2.markdown(f"<div class='metric-card'><div class='metric-title'>تێکڕای مامۆستایان</div><div class='metric-value'>{total_teachers}</div></div>", unsafe_allow_html=True)
    col_m3.markdown(f"<div class='metric-card'><div class='metric-title'>وانە بەردەستەکان</div><div class='metric-value'>{total_subs}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    menu = [
        "📊 داشبۆردی گشتی و گەڕان",
        "👨‍🎓 بەڕێوەبردن و لیستی قوتابیان",
        "📂 قوتابیان بەپێی ژوورەکان (1-20)",
        "📝 تۆمارکردنی نمرەی ڕۆژانە",
        "⚙️ بەڕێوەبردنی وانەکان",
        "👨‍🏫 تۆمارکردن و دەستکاریکردنی مامۆستایان", 
        "📅 تۆمارکردنی غیابات و ڕاپۆرت",
        "💯 نمرەی تاقیکردنەوە (30)", 
        "📄 کارتی A4 و ڕاپۆرت"
    ]
    
    choice = st.selectbox("بەشی داواکراو هەڵبژێرە:", menu)
    
    if st.button("🚪 دەرچوون (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("---")

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
                        c2.write(f"**شوێنی دانیشتن:** {st_data['address'] if st_data['address'] else 'دیاری نەکراوە'}")
                        
                        df_grades = get_student_grades_df(st_data['student_code'], conn)
                        st.dataframe(df_grades, use_container_width=True)
            else:
                st.warning("هیچ ئەنجامێک نەدۆزرایەوە.")

    elif choice == "👨‍🎓 بەڕێوەبردن و لیستی قوتابیان":
        st.subheader("👨‍🎓 بەڕێوەبردنی قوتابیان")
        tab_st1, tab_st2, tab_st3, tab_st4 = st.tabs(["📜 لیستی قوتابیان", "✏️ دەستکاریکردنی قوتابی", "➕ تۆمارکردنی یەک قوتابی", "📋 تۆمارکردنی بەکۆمەڵ"])

        with tab_st1:
            st.write("### 📜 لیستی گشتی قوتابیە تۆمارکراوەکان")
            query_st = """
                SELECT student_code as 'کۆدی قوتابی', full_name as 'ناوی تەواو', class_num as 'ژوور', phone as 'ژمارەی مۆبایل', address as 'شوێنی دانیشتن'
                FROM students ORDER BY class_num ASC
            """
            df_all_students = pd.read_sql_query(query_st, conn)
            if not df_all_students.empty:
                st.dataframe(df_all_students, use_container_width=True)
            else:
                st.info("هیچ قوتابییەک تا ئێستا تۆمار نەکراوە.")

        with tab_st2:
            st.write("### ✏️ دەستکاریکردن یان سڕینەوەی زانیارییەکانی قوتابی")
            c.execute("SELECT student_code, full_name, class_num, phone, address FROM students")
            st_list = c.fetchall()
            
            if st_list:
                st_dict = {f"{r['full_name']} (کۆد: {r['student_code']})": r for r in st_list}
                sel_edit = st.selectbox("قوتابی هەڵبژێرە بۆ دەستکاریکردن:", list(st_dict.keys()))
                edit_st = st_dict[sel_edit]

                st.info(f"دەستکاریکردنی زانیارییەکانی قوتابی: {edit_st['full_name']}")
                new_name = st.text_input("ناوی تەواوی قوتابی", value=edit_st['full_name'])
                
                ce1, ce2, ce3 = st.columns(3)
                new_cls = ce1.number_input("ژوور (1 تا 20)", min_value=1, max_value=20, value=int(edit_st['class_num']))
                new_phone = ce2.text_input("ژمارەی مۆبایل", value=edit_st['phone'] if edit_st['phone'] else "")
                new_addr = ce3.text_input("شوێنی دانیشتن", value=edit_st['address'] if edit_st['address'] else "")

                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("💾 چاککردن و پاشەکەوتکردن"):
                    c.execute("UPDATE students SET full_name=?, class_num=?, phone=?, address=? WHERE student_code=?", 
                              (new_name, new_cls, new_phone, new_addr, edit_st['student_code']))
                    conn.commit()
                    st.success("زانیارییەکانی قوتابی بە سەرکەوتوویی دەستکاری کران!")
                    st.rerun()

                if col_btn2.button("🗑️ سڕینەوەی ئەم قوتابییە"):
                    c.execute("DELETE FROM students WHERE student_code=?", (edit_st['student_code'],))
                    conn.commit()
                    st.warning(f"قوتابی ({edit_st['full_name']}) سڕایەوە!")
                    st.rerun()
            else:
                st.info("هیچ قوتابییەک بۆ دەستکاریکردن نەدۆزرایەوە.")

        with tab_st3:
            st.write("### ➕ تۆمارکردنی قوتابیی نوێ")
            if "auto_code" not in st.session_state:
                st.session_state.auto_code = ""

            def generate_next_code():
                c.execute("SELECT MAX(CAST(student_code AS INTEGER)) FROM students")
                max_code = c.fetchone()[0]
                if max_code is None:
                    st.session_state.auto_code = "1001"
                else:
                    st.session_state.auto_code = str(max_code + 1)

            c1, c2 = st.columns([3, 1])
            with c1:
                code = st.text_input("کۆدی قوتابی", value=st.session_state.auto_code)
            with c2:
                st.write(" ")
                st.write(" ")
                if st.button("🎲 داواکردنی کۆدی نوێ"):
                    generate_next_code()
                    st.rerun()

            name = st.text_input("ناوی تەواوی قوتابی", key="add_name")
            
            c3, c4, c5 = st.columns(3)
            cls = c3.number_input("ژوور (1 تا 20)", min_value=1, max_value=20, step=1, key="add_cls")
            phone = c4.text_input("ژمارەی مۆبایل", key="add_phone")
            address = c5.text_input("شوێنی دانیشتن (ناونیشان)", key="add_addr")

            if st.button("💾 پاشەکەوتکردنی قوتابی"):
                if code and name:
                    try:
                        c.execute("INSERT INTO students VALUES (?,?,?,?,?,?)", (code, name, "", int(cls), address, phone))
                        conn.commit()
                        st.success(f"قوتابی ({name}) بە سەرکەوتوویی تۆمارکرا!")
                        st.session_state.auto_code = ""
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("ئەم کۆدە پێشتر بۆ قوتابییەکی تر بەکارهاتووە! کلیک لە 'داواکردنی کۆدی نوێ' بکە.")
                else:
                    st.error("تکایە بەلایەنی کەمەوە ناو و کۆد بنووسە.")

        with tab_st4:
            st.write("### 📋 تۆمارکردنی بەکۆمەڵ")
            cls_bulk = st.number_input("ژوور (1 تا 20)", min_value=1, max_value=20, step=1, key="bulk_cls")
            start_code = st.number_input("کۆدی دەستپێک", min_value=1, value=100)
            raw_names = st.text_area("لیستی ناوەکان پەیست بکه (هر ناوێک لە دێڕێکدا):", height=150)

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
                st.success("ناوەکان بە سەرکەوتوویی لە داتابەیس پاشەکەوت کران!")
                st.rerun()

    elif choice == "📂 قوتابیان بەپێی ژوورەکان (1-20)":
        st.subheader("🏢 شیت و لیستی قوتابیان بەپێی ژوور")
        selected_room = st.selectbox("ژوور هەڵبژێرە:", list(range(1, 21)))
        
        c.execute("SELECT student_code as 'کۆد', full_name as 'ناوی تەواو', phone as 'مۆبایل', address as 'شوێنی دانیشتن' FROM students WHERE class_num=?", (selected_room,))
        room_students = c.fetchall()
        
        if room_students:
            st.dataframe(pd.DataFrame(room_students), use_container_width=True)
        else:
            st.info("ئەم ژوورە بەتاڵە.")

    elif choice == "📝 تۆمارکردنی نمرەی ڕۆژانە":
        st.subheader("📝 تۆمارکردن و بینینی نمرەی ڕۆژانەی قوتابیان")
        tab1, tab2 = st.tabs(["➕ تۆمارکردنی نمرە", "📜 مێژووی نمرەکان"])
        
        with tab1:
            c.execute("SELECT student_code, full_name, class_num FROM students")
            all_st = c.fetchall()
            if all_st:
                st_dict = {f"{r['full_name']} (ژووری {r['class_num']})": r['student_code'] for r in all_st}
                selected_st = st.selectbox("ناوی قوتابی هەڵبژێرە:", list(st_dict.keys()))
                st_code = st_dict[selected_st]
                
                c1, c2 = st.columns(2)
                sub_name = c1.selectbox("بابەت / وانە:", get_all_subjects())
                term = c2.selectbox("وەرز:", [1, 2])
                
                c3, c4 = st.columns(2)
                mark_date = c3.date_input("ڕێکەوتی ڕۆژانە:", datetime.now())
                daily_mark = c4.number_input("نمرە (0 تا 20):", min_value=0.0, max_value=20.0, step=0.5)
                
                if st.button("پاشەکەوتکردنی نمرەی ڕۆژانە"):
                    c.execute("INSERT INTO daily_marks (student_code, subject_name, term, mark, date) VALUES (?,?,?,?,?)",
                              (st_code, sub_name, term, daily_mark, str(mark_date)))
                    conn.commit()
                    st.success("نمرەی ڕۆژانە بە سەرکەوتوویی پاشەکەوت کرا!")

        with tab2:
            st.write("### بینینی نمرە تۆمارکراوەکانی قوتابی")
            c.execute("SELECT student_code, full_name FROM students")
            st_map2 = {f"{r['full_name']} ({r['student_code']})": r['student_code'] for r in c.fetchall()}
            if st_map2:
                sel_st2 = st.selectbox("قوتابی هەڵبژێرە بۆ بینینی نمرەکانی:", list(st_map2.keys()))
                code_st2 = st_map2[sel_st2]
                
                query = """
                    SELECT date as 'ڕێکەوت', subject_name as 'وانە', term as 'وەرز', mark as 'نمرە'
                    FROM daily_marks WHERE student_code=? ORDER BY date DESC
                """
                df_daily = pd.read_sql_query(query, conn, params=(code_st2,))
                st.dataframe(df_daily, use_container_width=True)

    elif choice == "⚙️ بەڕێوەبردنی وانەکان":
        st.subheader("⚙️ بەڕێوەبردنی وانەکان")
        all_subs = get_all_subjects()
        st.write("**وانە چالاکەکان:** ", ", ".join(all_subs))
        
        c1, c2 = st.columns(2)
        new_s = c1.text_input("وانەی نوێ:")
        if c1.button("زیادکردن"):
            if new_s:
                c.execute("INSERT OR IGNORE INTO custom_subjects (subject_name) VALUES (?)", (new_s,))
                conn.commit()
                st.rerun()

        del_s = c2.selectbox("وانە بۆ سڕینەوە:", all_subs)
        if c2.button("سڕینەوە"):
            c.execute("DELETE FROM custom_subjects WHERE subject_name=?", (del_s,))
            conn.commit()
            st.rerun()

    elif choice == "👨‍🏫 تۆمارکردن و دەستکاریکردنی مامۆستایان":
        st.subheader("👨‍🏫 بەڕێوەبردنی مامۆستایان")
        
        tab_t1, tab_t2, tab_t3 = st.tabs(["📜 لیستی مامۆستایان", "✏️ دەستکاریکردنی مامۆستا", "➕ تۆمارکردنی مامۆستای نوێ"])
        
        with tab_t1:
            st.write("### 📜 لیستی هەموو مامۆستایان")
            query_t = """
                SELECT teacher_code as 'کۆد', full_name as 'ناوی تەواو', username as 'ناوی بەکارهێنەر', assigned_subjects as 'ژوور و وانەکان'
                FROM teachers
            """
            df_teachers = pd.read_sql_query(query_t, conn)
            if not df_teachers.empty:
                st.dataframe(df_teachers, use_container_width=True)
            else:
                st.info("هیچ مامۆستایەک تا ئێستا تۆمار نەکراوە.")

        with tab_t2:
            st.write("### ✏️ دەستکاریکردنی زانیاریی مامۆستا (ناو، ژوور و وانەکان)")
            c.execute("SELECT * FROM teachers")
            t_rows = c.fetchall()
            if t_rows:
                t_dict = {f"{r['full_name']} (کۆد: {r['teacher_code']})": r for r in t_rows}
                sel_t_edit = st.selectbox("مامۆستا هەڵبژێرە:", list(t_dict.keys()))
                e_teacher = t_dict[sel_t_edit]

                t_name_edit = st.text_input("ناوی تەواوی مامۆستا", value=e_teacher['full_name'])
                t_user_edit = st.text_input("ناوی بەکارهێنەر (Username)", value=e_teacher['username'])
                t_pass_edit = st.text_input("وشەی نهێنی نوێ", value=e_teacher['password'])

                all_subs = get_all_subjects()
                
                # Parsing existing assignment
                parsed_t = []
                if e_teacher['assigned_subjects']:
                    for item in e_teacher['assigned_subjects'].split('|'):
                        if ':' in item:
                            cs, ss = item.split(':')
                            parsed_t.append((int(cs.strip()), ss.strip()))

                c_cls1 = parsed_t[0][0] if len(parsed_t) > 0 else 1
                c_sub1 = parsed_t[0][1] if len(parsed_t) > 0 and parsed_t[0][1] in all_subs else all_subs[0]
                c_cls2 = parsed_t[1][0] if len(parsed_t) > 1 else 1
                c_sub2 = parsed_t[1][1] if len(parsed_t) > 1 and parsed_t[1][1] in all_subs else all_subs[0]

                ce_col1, ce_col2 = st.columns(2)
                edit_cls1 = ce_col1.number_input("ژووری یەکەم", min_value=1, max_value=20, value=c_cls1, key="e_cls1")
                edit_sub1 = ce_col1.selectbox("وانەی یەکەم", all_subs, index=all_subs.index(c_sub1) if c_sub1 in all_subs else 0, key="e_sub1")

                edit_cls2 = ce_col2.number_input("ژووری دووەم", min_value=1, max_value=20, value=c_cls2, key="e_cls2")
                edit_sub2 = ce_col2.selectbox("وانەی دووەم", all_subs, index=all_subs.index(c_sub2) if c_sub2 in all_subs else 0, key="e_sub2")

                btn_e1, btn_e2 = st.columns(2)
                if btn_e1.button("💾 پاشەکەوتکردنی گۆڕانکارییەکان"):
                    sub_str_new = f"{edit_cls1}:{edit_sub1}|{edit_cls2}:{edit_sub2}"
                    c.execute("""UPDATE teachers SET full_name=?, username=?, password=?, assigned_classes=?, assigned_subjects=? 
                                 WHERE teacher_code=?""", 
                              (t_name_edit, t_user_edit, t_pass_edit, f"{edit_cls1},{edit_cls2}", sub_str_new, e_teacher['teacher_code']))
                    conn.commit()
                    st.success("زانیارییەکانی مامۆستا دەستکاری کران!")
                    st.rerun()

                if btn_e2.button("🗑️ سڕینەوەی ئەم مامۆستایە"):
                    c.execute("DELETE FROM teachers WHERE teacher_code=?", (e_teacher['teacher_code'],))
                    conn.commit()
                    st.warning("مامۆستاکە سڕایەوە!")
                    st.rerun()
            else:
                st.info("هیچ مامۆستایەک نییە بۆ دەستکاریکردن.")

        with tab_t3:
            c1, c2 = st.columns(2)
            code = c1.text_input("کۆدی مامۆستا")
            name = c2.text_input("ناوی تەواو")
            uname = c1.text_input("ناوی بەکارهێنەر (Username)", key="new_u")
            pwd = c2.text_input("وشەی نهێنی (Password)", type="password", key="new_p")

            all_subs = get_all_subjects()
            cls1 = c1.number_input("ژووری یەکەم", min_value=1, max_value=20)
            sub1 = c1.selectbox("وانەی یەکەم", all_subs, key="m_sub1")
            
            cls2 = c2.number_input("ژووری دووەم", min_value=1, max_value=20)
            sub2 = c2.selectbox("وانەی دووەم", all_subs, key="m_sub2")

            if st.button("زیادکردنی مامۆستا"):
                if code and name and uname and pwd:
                    sub_str = f"{cls1}:{sub1}|{cls2}:{sub2}"
                    c.execute("INSERT INTO teachers (teacher_code, full_name, username, password, assigned_classes, assigned_subjects) VALUES (?,?,?,?,?,?)",
                              (code, name, uname, pwd, f"{cls1},{cls2}", sub_str))
                    conn.commit()
                    st.success("مامۆستا بە سەرکەوتوویی تۆمارکرا!")
                    st.rerun()
                else:
                    st.error("تکایە هەموو بڕگەکان پڕبکەرەوە.")

    elif choice == "📅 تۆمارکردنی غیابات و ڕاپۆرت":
        st.subheader("📅 بەڕێوەبردنی ئامادەبوون، غیابات و مۆڵەت")
        tab_att1, tab_att2 = st.tabs(["➕ تۆمارکردنی غیاب/مۆڵەت", "📊 ڕاپۆرتی غیابات بەپێی ژوور"])

        with tab_att1:
            st.write("### تۆمارکردنی غیابی قوتابییەکی دیاریکراو")
            c.execute("SELECT student_code, full_name, class_num FROM students")
            all_st_att = c.fetchall()
            
            if all_st_att:
                dict_att = {f"{r['full_name']} (ژووری {r['class_num']})": r['student_code'] for r in all_st_att}
                selected_st_att = st.selectbox("ناوی قوتابییەکە بنووسە یان هەڵبژێرە:", list(dict_att.keys()))
                scode_att = dict_att[selected_st_att]
                
                ca1, ca2 = st.columns(2)
                att_date = ca1.date_input("ڕێکەوت:", datetime.now())
                att_status = ca2.selectbox("دۆخ:", ["نەهاتوو (غیاب)", "مۆڵەت", "هاتوو"])
                att_notes = st.text_input("تێبینی (ئارەزوومەندانه):")
                
                if st.button("تۆمارکردنی دۆخی غیاب"):
                    c.execute("INSERT INTO attendance (student_code, date, status, notes) VALUES (?,?,?,?)",
                              (scode_att, str(att_date), att_status, att_notes))
                    conn.commit()
                    st.success(f"دۆخی ({att_status}) بۆ قوتابییەکە بە سەرکەوتوویی تۆمارکرا!")

        with tab_att2:
            st.write("### بینینی ڕاپۆرتی غیابات و مۆڵەت")
            col_r1, col_r2 = st.columns(2)
            search_room = col_r1.number_input("ژوور هەڵبژێرە (1 تا 20):", min_value=1, max_value=20, value=1)
            filter_status = col_r2.selectbox("فلتەر بەپێی دۆخ:", ["هەمووی", "نەهاتوو (غیاب)", "مۆڵەت", "هاتوو"])
            
            query_att = """
                SELECT a.date as 'ڕێکەوت', s.full_name as 'ناوی قوتابی', s.class_num as 'ژوور', a.status as 'دۆخ', a.notes as 'تێبینی'
                FROM attendance a
                JOIN students s ON a.student_code = s.student_code
                WHERE s.class_num = ?
            """
            params = [search_room]
            if filter_status != "هەمووی":
                query_att += " AND a.status = ?"
                params.append(filter_status)
                
            query_att += " ORDER BY a.date DESC"
            
            df_att_report = pd.read_sql_query(query_att, conn, params=params)
            if not df_att_report.empty:
                st.dataframe(df_att_report, use_container_width=True)
            else:
                st.info("هیچ داتایەک بۆ ئەم ژوورە نەدۆزرایەوە.")

    elif choice == "💯 نمرەی تاقیکردنەوە (30)":
        st.subheader("💯 نمرەی تاقیکردنەوە (30)")
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
                <p><b>ناوی قوتابی:</b> {s_data['full_name']} | <b>کۆد:</b> {s_data['student_code']} | <b>ژوور:</b> {s_data['class_num']} | <b>شوێنی دانیشتن:</b> {s_data['address']}</p>
                <hr>
            </div>
            """, unsafe_allow_html=True)
            st.dataframe(df_g, use_container_width=True)

    conn.close()

# 5. دەستەی مامۆستا (Teacher Dashboard)
def teacher_dashboard():
    t_info = st.session_state.user_info
    st.title(f"👨‍🏫 بەخێربێیت مامۆستا {t_info['full_name']}")
    
    if st.button("🚪 دەرچوون"):
        st.session_state.logged_in = False
        st.rerun()

    raw_subs = t_info.get('assigned_subjects', '')
    parsed = []
    if raw_subs:
        for item in raw_subs.split('|'):
            if ':' in item:
                c_str, s_str = item.split(':')
                parsed.append((int(c_str.strip()), s_str.strip()))

    if not parsed:
        st.warning("هیچ پۆل یان وانەیەک بۆ تۆ لەلایەن بەڕێوەبەرەوە دیاری نەکراوە!")
        return

    st.markdown("---")
    
    t_menu = ["📝 تۆمارکردنی نمرەی ڕۆژانە", "📂 قوتابیانی پۆلەکەم", "📅 تۆمارکردنی غیابات"]
    t_choice = st.radio("دیاری کردنی بەش:", t_menu, horizontal=True)

    opts = [f"ژووری {c_num} - وانەی: {s_num}" for c_num, s_num in parsed]
    sel = st.selectbox("پۆل و وانەی دیاریکراو هەڵبژێرە:", opts)
    idx = opts.index(sel)
    target_cls, target_sub = parsed[idx]

    conn = get_db_connection()
    c = conn.cursor()

    if t_choice == "📝 تۆمارکردنی نمرەی ڕۆژانە":
        st.subheader(f"📝 تۆمارکردنی نمرەی ڕۆژانە بۆ (ژووری {target_cls} - {target_sub})")
        
        m_date = st.date_input("ڕێکەوت:", datetime.now())
        term = st.selectbox("وەرز", [1, 2])

        c.execute("SELECT student_code, full_name FROM students WHERE class_num=?", (target_cls,))
        st_in_cls = c.fetchall()

        if st_in_cls:
            marks = {}
            for r in st_in_cls:
                c1, c2 = st.columns([2, 2])
                c1.write(f"👤 **{r['full_name']}**")
                marks[r['student_code']] = c2.number_input("نمرەی ئەمڕۆ", min_value=0.0, max_value=20.0, step=0.5, key=f"tm_{r['student_code']}")
            
            if st.button("پاشەکەوتکردنی نمرەکان"):
                for scode, smark in marks.items():
                    c.execute("INSERT INTO daily_marks (student_code, subject_name, term, mark, date) VALUES (?,?,?,?,?)",
                              (scode, target_sub, term, smark, str(m_date)))
                conn.commit()
                st.success("نمرەکان بە سەرکەوتوویی پاشەکەوت کران!")
        else:
            st.info("هیچ قوتابییەک لەم ژوورەدا نییە.")

    elif t_choice == "📂 قوتابیانی پۆلەکەم":
        st.subheader(f"👥 لیستی قوتابیانی ژووری ({target_cls})")
        students_df = pd.read_sql_query(f"SELECT student_code as 'کۆدی قوتابی', full_name as 'ناوی قوتابی', phone as 'مۆبایل', address as 'شوێنی دانیشتن' FROM students WHERE class_num={target_cls}", conn)
        if not students_df.empty:
            st.dataframe(students_df, use_container_width=True)
        else:
            st.info("هیچ قوتابییەک لەم ژوورەدا نەدۆزرایەوە.")

    elif t_choice == "📅 تۆمارکردنی غیابات":
        st.subheader(f"📅 تۆمارکردنی غیابات بۆ قوتابیانی (ژووری {target_cls})")
        
        c.execute("SELECT student_code, full_name FROM students WHERE class_num=?", (target_cls,))
        students_list = c.fetchall()
        
        if students_list:
            st_dict = {r['full_name']: r['student_code'] for r in students_list}
            sel_st = st.selectbox("قوتابی هەڵبژێرە:", list(st_dict.keys()))
            scode = st_dict[sel_st]
            
            ca1, ca2 = st.columns(2)
            att_date = ca1.date_input("ڕێکەوت:", datetime.now(), key="t_att_date")
            att_status = ca2.selectbox("دۆخ:", ["نەهاتوو (غیاب)", "مۆڵەت", "هاتوو"], key="t_att_status")
            att_notes = st.text_input("تێبینی:", key="t_att_notes")
            
            if st.button("پاشەکەوتکردنی غیاب"):
                c.execute("INSERT INTO attendance (student_code, date, status, notes) VALUES (?,?,?,?)",
                          (scode, str(att_date), att_status, att_notes))
                conn.commit()
                st.success("غیابات بە سەرکەوتوویی تۆمارکرا!")

    conn.close()

# 6. ڕاڕەوی سەرەکی
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Admin":
        admin_dashboard()
    else:
        teacher_dashboard()
