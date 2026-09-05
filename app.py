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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==========================================
# 1. پێناسکردنی فۆنت و نەخشەکانی PDF
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
# 2. نەخشی بەرهەمهێنانی فایلی Excel
# ==========================================
def export_all_data_to_excel(conn):
    output = io.BytesIO()
    
    df_students = pd.read_sql_query("""
        SELECT student_code AS 'کۆدی قوتابی', full_name AS 'ناوی تەواو', 
               class_num AS 'ژوور', phone AS 'مۆبایل', address AS 'ناونیشان'
        FROM students ORDER BY class_num, student_code
    """, conn)
    
    df_daily = pd.read_sql_query("""
        SELECT d.student_code AS 'کۆدی قوتابی', s.full_name AS 'ناوی قوتابی', s.class_num AS 'ژوور',
               d.subject_name AS 'بابەت', d.term AS 'وەرز', d.mark AS 'نمرە', d.date AS 'ڕێکەوت'
        FROM daily_marks d
        JOIN students s ON d.student_code = s.student_code
        ORDER BY d.date DESC
    """, conn)
    
    df_exam = pd.read_sql_query("""
        SELECT e.student_code AS 'کۆدی قوتابی', s.full_name AS 'ناوی قوتابی', s.class_num AS 'ژوور',
               e.subject_name AS 'بابەت', e.term AS 'وەرز', e.exam_score AS 'نمرەی تاقیکردنەوە'
        FROM exam_marks e
        JOIN students s ON e.student_code = s.student_code
        ORDER BY s.class_num, e.student_code
    """, conn)

    df_attendance = pd.read_sql_query("""
        SELECT a.student_code AS 'کۆدی قوتابی', s.full_name AS 'ناوی قوتابی', s.class_num AS 'ژوور',
               a.date AS 'ڕێکەوت', a.status AS 'دۆخ', a.notes AS 'تێبینی'
        FROM attendance a
        JOIN students s ON a.student_code = s.student_code
        ORDER BY a.date DESC
    """, conn)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_students.to_excel(writer, sheet_name='لیستی قوتابیان', index=False)
        df_daily.to_excel(writer, sheet_name='نمرەی ڕۆژانە', index=False)
        df_exam.to_excel(writer, sheet_name='نمرەی تاقیکردنەوە', index=False)
        df_attendance.to_excel(writer, sheet_name='غیابات و مۆڵەت', index=False)

    output.seek(0)
    return output


# ==========================================
# 3. بنکەدراوە و ڕووکاری Streamlit
# ==========================================
conn = sqlite3.connect("quran_center.db", check_same_thread=False)

def admin_dashboard():
    st.title("👨‍💼 داشبۆردی بەڕێوەبەر")
    
    st.subheader("🔎 گەڕانی خێرا و بینینی زانیاری قوتابی")
    search_term = st.text_input("ناوی قوتابی یاخود کۆد بنووسە:")
    
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
