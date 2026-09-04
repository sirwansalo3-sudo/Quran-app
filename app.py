import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="سیستەمی بنکەی قورئان", layout="wide", page_icon="📖")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame()

def save_data(df, sheet_name):
    conn.update(worksheet=sheet_name, data=df)

st.markdown("""
    <style>
    .stMainBlockContainer { direction: RTL; text-align: right; }
    .stApp { background-color: #f8fafc; }
    </style>
""", unsafe_allow_html=True)

df_students = load_data("Students")
if df_students.empty:
    df_students = pd.DataFrame(columns=["کۆدی قوتابی", "ناوی تەواو", "ژوور", "ژمارەی مۆبایل", "شوێنی دانیشتن"])
    save_data(df_students, "Students")

st.title("📖 سیستەمی بەڕێوەبردنی بنکەی قورئان (Google Sheets)")
st.success("✅ داتاکانت ئۆنلاینن و هەرگیز ڕەش نابنەوە!")

tab1, tab2, tab3 = st.tabs(["📜 لیستی قوتابیان", "➕ تۆمارکردنی قوتابی", "✏️ دەستکاریکردن یان سڕینەوە"])

with tab1:
    st.subheader("📜 قوتابییە تۆمارکراوەکان")
    df_curr = load_data("Students")
    if not df_curr.empty:
        st.dataframe(df_curr, use_container_width=True)
    else:
        st.info("هیچ قوتابییەک تا ئێستا تۆمار نەکراوە.")

with tab2:
    st.subheader("➕ تۆمارکردنی قوتابیی نوێ")
    with st.form("add_student_form"):
        code = st.text_input("کۆدی قوتابی")
        name = st.text_input("ناوی تەواوی قوتابی")
        cls = st.number_input("ژوور (1 تا 20)", min_value=1, max_value=20, value=1)
        phone = st.text_input("ژمارەی مۆبایل")
        address = st.text_input("شوێنی دانیشتن")
        
        submit = st.form_submit_button("💾 پاشەکەوتکردن لە Google Sheet")
        
        if submit:
            if code and name:
                df_curr = load_data("Students")
                new_row = pd.DataFrame([{
                    "کۆدی قوتابی": str(code),
                    "ناوی تەواو": name,
                    "ژوور": int(cls),
                    "ژمارەی مۆبایل": phone,
                    "شوێنی دانیشتن": address
                }])
                df_updated = pd.concat([df_curr, new_row], ignore_index=True)
                save_data(df_updated, "Students")
                st.success(f"قوتابی ({name}) بە سەرکەوتوویی پاشەکەوت کرا!")
                st.rerun()
            else:
                st.error("تکایە ناو و کۆد پڕبکەرەوە.")

with tab3:
    st.subheader("✏️ دەستکاریکردن / سڕینەوە")
    df_curr = load_data("Students")
    if not df_curr.empty:
        st_list = df_curr["کۆدی قوتابی"].tolist()
        selected_code = st.selectbox("کۆدی قوتابی هەڵبژێرە:", st_list)
        
        student_row = df_curr[df_curr["کۆدی قوتابی"] == selected_code].iloc[0]
        
        edit_name = st.text_input("ناوی تەواو", value=student_row["ناوی تەواو"])
        edit_cls = st.number_input("ژوور", min_value=1, max_value=20, value=int(student_row["ژوور"]))
        edit_phone = st.text_input("مۆبایل", value=str(student_row["ژمارەی مۆبایل"]))
        edit_addr = st.text_input("ناونیشان", value=str(student_row["شوێنی دانیشتن"]))
        
        col_btn1, col_btn2 = st.columns(2)
        
        if col_btn1.button("💾 نوێکردنەوەی زانیاری"):
            df_curr.loc[df_curr["کۆدی قوتابی"] == selected_code, ["ناوی تەواو", "ژوور", "ژمارەی مۆبایل", "شوێنی دانیشتن"]] = [edit_name, edit_cls, edit_phone, edit_addr]
            save_data(df_curr, "Students")
            st.success("زانیارییەکان نوێکرانەوە!")
            st.rerun()
            
        if col_btn2.button("🗑️ سڕینەوەی قوتابی"):
            df_filtered = df_curr[df_curr["کۆدی قوتابی"] != selected_code]
            save_data(df_filtered, "Students")
            st.warning("قوتابییەکە سڕایەوە!")
            st.rerun()
