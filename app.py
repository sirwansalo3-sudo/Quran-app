import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="سیستەمی بنکەی قورئان", layout="wide", page_icon="📖")

# بەستنەوە بە Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # خوێندنەوەی داتاکان لە شێوەی DataFrame
        df = conn.read(worksheet="Students", ttl=0)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=["کۆدی قوتابی", "ناوی تەواو", "ژوور", "ژمارەی مۆبایل", "شوێنی دانیشتن"])

st.markdown("""
    <style>
    .stMainBlockContainer { direction: RTL; text-align: right; }
    .stApp { background-color: #f8fafc; }
    </style>
""", unsafe_allow_html=True)

st.title("📖 سیستەمی بەڕێوەبردنی بنکەی قورئان")

tab1, tab2 = st.tabs(["📜 لیستی قوتابیان", "➕ تۆمارکردنی قوتابیی نوێ"])

with tab1:
    st.subheader("📜 قوتابییە تۆمارکراوەکان")
    if st.button("🔄 نوێکردنەوەی داتاکان"):
        st.cache_data.clear()
        st.rerun()
        
    df_curr = load_data()
    if not df_curr.empty:
        st.dataframe(df_curr, use_container_width=True)
    else:
        st.info("هیچ داتایەک نەدۆزرایەوە.")

with tab2:
    st.subheader("➕ تۆمارکردنی قوتابیی نوێ")
    with st.form("add_student_form"):
        code = st.text_input("کۆدی قوتابی")
        name = st.text_input("ناوی تەواوی قوتابی")
        cls = st.number_input("ژوور (1 تا 20)", min_value=1, max_value=20, value=1)
        phone = st.text_input("ژمارەی مۆبایل")
        address = st.text_input("شوێنی دانیشتن")
        
        submit = st.form_submit_button("💾 پاشەکەوتکردن")
        
        if submit:
            if code and name:
                df_curr = load_data()
                new_row = pd.DataFrame([{
                    "کۆدی قوتابی": str(code),
                    "ناوی تەواو": name,
                    "ژوور": int(cls),
                    "ژمارەی مۆبایل": phone,
                    "شوێنی دانیشتن": address
                }])
                df_updated = pd.concat([df_curr, new_row], ignore_index=True)
                
                # نوێکردنەوەی Sheet
                conn.update(worksheet="Students", data=df_updated)
                st.success(f"قوتابی ({name}) بە سەرکەوتوویی تۆمارکرا!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("تکایە ناو و کۆد پڕبکەرەوە.")
