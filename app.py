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
# 1. بەشی دروستکردنی ڕاپۆرتی PDF (بە فۆنتی ڕاستکراوە)
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
        'ArabicTitle',
        fontName=FONT_NAME,
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        alignment=1,
        spaceAfter=15
    )
    
    header_style = ParagraphStyle(
        'ArabicHeader',
        fontName=FONT_NAME,
        fontSize=11,
        leading=14,
        textColor=colors.white,
        alignment=1
    )
    
    cell_style = ParagraphStyle(
        'ArabicCell',
        fontName=FONT_NAME,
        fontSize=10,
        leading=13,
        textColor=TEXT_COLOR,
        alignment=1
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
    elements.append(Spacer(1, 20))

    if not df_g.empty:
        table_data = [[
            Paragraph(reshape_txt("کۆی گشتی (50)"), header_style),
            Paragraph(reshape_txt("تاقیکردنەوە (30)"), header_style),
            Paragraph(reshape_txt("ڕۆژانە (20)"), header_style),
            Paragraph(reshape_txt("وەرز"), header_style),
            Paragraph(reshape_txt("وانی / بابەت"), header_style),
        ]]
        
        for _, r in df_g.iterrows():
            table_data.append([
                Paragraph(reshape_txt(str(r.get('کۆی گشتی (50)', ''))), cell_style),
                Paragraph(reshape_txt(str(r.get('تاقیکردنەوە (30)', ''))), cell_style),
                Paragraph(reshape_txt(str(r.get('کۆی ڕۆژانە (20)', ''))), cell_style),
                Paragraph(reshape_txt(str(r.get('وەرز', ''))), cell_style),
                Paragraph(reshape_txt(str(r.get('وانە / بابەت', ''))), cell_style),
            ])
        
        t_marks = Table(table_data, colWidths=[90, 90, 90, 60, 170])
        t_marks.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, SECONDARY_COLOR]),
            ('PADDING', (0,0), (-1,-1), 7),
        ]))
        elements.append(t_marks)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================================
# 2. بەشی دابەزاندنی ئەکسل (بەبێ تێکچوونی داتابەیس)
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
# 3. بەشی کارپێکردنی بەرنامەکە (Streamlit)
# ==========================================
conn = sqlite3.connect("quran_center.db", check_same_thread=False)

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
    admin_dashboard()

if __name__ == "__main__":
    main()
