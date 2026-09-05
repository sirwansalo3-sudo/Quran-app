import io
import os
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# کتێبخانەکانی پەیوەندیدار بە PDF و فۆنتی کوردی
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle

# ==========================================
# 1. ڕێکخستنی لاپەڕە و دیزاینی CSS
# ==========================================
st.set_page_config(
    page_title="سیستەمی قوتابخانەی قورئان",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# دیزاینی نەرم و مۆدێرن بە جێبەجێکردنی CSS
st.markdown("""
    <style>
    .main {
        direction: rtl;
        text-align: right;
    }
    div.stButton > button {
        width: 100%;
        background-color: #0f766e;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #115e59;
        color: white;
    }
    .stDownloadButton > button {
        width: 100%;
        background-color: #0284c7;
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-weight: bold;
        border: none;
    }
    .stDownloadButton > button:hover {
        background-color: #0369a1;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. دروستکردنی کارتی PDF
# ==========================================
FONT_PATH = "NotoNaskhArabic-Regular.ttf"
FONT_NAME = "KurdishFont"

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
else:
    FONT_NAME = "Helvetica"

PRIMARY_COLOR = colors.HexColor("#0f766e")
SECONDARY_COLOR = colors.HexColor("#f0fdf4")
TEXT_COLOR = colors.HexColor("#1e293b")
BORDER_COLOR = colors.HexColor("#cbd5e1")

def reshape_txt(text):
    if not text or FONT_NAME == "Helvetica":
        return str(text)
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)

def generate_a4_pdf(s_data, df_g):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    elements = []
    
    title_style = ParagraphStyle(
        'ArabicTitle', fontName=FONT_NAME, fontSize=20, leading=24,
        textColor=PRIMARY_COLOR, alignment=1, spaceAfter=15
    )
    cell_style = ParagraphStyle(
        'ArabicCell', fontName=FONT_NAME, fontSize=10, leading=13,
        textColor=TEXT_COLOR, alignment=1
    )

    elements.append(Paragraph(reshape_txt("📖 بنکەی قورئانی پیرۆز - کارتی ئەنجامی قوتابی"), title_style))
    elements.append(Spacer(1, 10))

    info_data = [
        [
            Paragraph(reshape_txt(s_data.get('full_name', '')), cell_style),
            Paragraph(reshape_txt("ناوی قوتابی:"), cell_style),
            Paragraph(reshape_txt(str(s_data.get('student_code', ''))), cell_style),
            Paragraph(reshape_txt("کۆدی قوتابی:"), cell_style),
        ],
        [
            Paragraph(reshape_txt(str(s_data.get('address', '-') if s_data.get('address') else '-')), cell_style),
            Paragraph(reshape_txt("ناونیشان:"), cell_style),
            Paragraph(reshape_txt(str(s_data.get('class_num', ''))), cell_style),
            Paragraph(reshape_txt("ژوور / پۆل:"), cell_style),
        ]
    ]
    
    t_info = Table(info_data, colWidths=[160, 90, 160, 90])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (1,0), (1,-1), SECONDARY_COLOR),
        ('BACKGROUND', (3,0), (3,-1), SECONDARY_COLOR),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_info)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================
# 3. بەشی دابەزاندنی Excel (بەبێ کێشەی DatabaseError)
# ==========================================
def export_all_data_to_excel(conn):
    output = io.BytesIO()
    
    def safe_read_sql(query, conn):
        try:
            return pd.read_sql_query(query, conn)
        except Exception:
            return pd.DataFrame()

    df_students = safe_read_sql("SELECT * FROM students", conn)
    df_daily = safe_read_sql("SELECT * FROM daily_marks", conn)
    df_exam = safe_read_sql("SELECT * FROM exam_marks", conn)
    df_attendance = safe_read_sql("SELECT * FROM attendance", conn)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not df_students.empty:
            df_students.to_excel(writer, sheet_name='لیستی قوتابیان', index=False)
        else:
            pd.DataFrame({'پەیام': ['هیچ زانیارییەک نییە']}).to_excel(writer, sheet_name='لیستی قوتابیان', index=False)
            
        if not df_daily.empty:
            df_daily.to_excel(writer, sheet_name='نمرەی ڕۆژانە', index=False)
            
        if not df_exam.empty:
            df_exam.to_excel(writer, sheet_name='نمرەی تاقیکردنەوە', index=False)
            
        if not df_attendance.empty:
            df_attendance.to_excel(writer, sheet_name='غیابات', index=False)

    output.seek(0)
    return output

# ==========================================
# 4. دەستپێکردنی داتابەیس و ڕووکاری پڕۆگرامەکە
# ==========================================
conn = sqlite3.connect("quran_center.db", check_same_thread=False)

def student_view():
    st.title("🎓 بەشی قوتابیان و ئەنجامەکان")
    st.subheader("🔎 گەڕان بەدوای نمرەی قوتابی")
    
    code_input = st.text_input("کۆدی قوتابی بنووسە:")
    if code_input:
        st.info(f"ئەنجامەکانی کۆدی: {code_input}")

def admin_dashboard():
    st.title("👨‍💼 داشبۆردی بەڕێوەبەر")
    
    st.subheader("🔎 گەڕانی خێرا و بینینی زانیاری قوتابی")
    st.text_input("ناوی قوتابی یاخود کۆد بنووسە:")
    
    st.markdown("---")
    st.subheader("📥 دابەزاندنی تەواوی زانیارییەکانی سیستەم")

    excel_file = export_all_data_to_excel(conn)

    st.download_button(
        label="📊 داونلۆدکردنی هەموو زانیارییەکان بە فۆرماتی Excel",
        data=excel_file,
        file_name=f"Quran_Center_Data_{datetime.now().strftime('%Y_%m_%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def main():
    st.sidebar.title("📌 مێنیوی سەرەکی")
    
    menu_choice = st.sidebar.radio(
        "بەشێک هەڵبژێرە:",
        ["🎓 بەشی قوتابیان", "🔐 چوونەژوورەوەی بەڕێوەبەر"]
    )

    if menu_choice == "🎓 بەشی قوتابیان":
        student_view()

    elif menu_choice == "🔐 چوونەژوورەوەی بەڕێوەبەر":
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False

        if not st.session_state.logged_in:
            st.subheader("🔑 چوونەژوورەوەی بەڕێوەبەر")
            username = st.text_input("ناوی بەکارهێنەر:")
            password = st.text_input("وێنەی نهێنی (Password):", type="password")
            
            if st.button("چوونەژوورەوە"):
                # پاسوۆردەکە دانراوە لەسەر admin123
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.success("بە سەرکەوتوویی چوویته ژوورەوە!")
                    st.rerun()
                else:
                    st.error("ناوی بەکارهێنەر یان پاسوۆرد هەڵەیە!")
        else:
            if st.sidebar.button("دەربازبوون / Logout"):
                st.session_state.logged_in = False
                st.rerun()
            admin_dashboard()

if __name__ == "__main__":
    main()
