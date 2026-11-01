
from flask import Blueprint, send_file, redirect, url_for, session, flash
from db import get_connection
from io import BytesIO
import pandas as pd

exports = Blueprint("exports", __name__)


def get_loan_data():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            l.loan_id,
            b.title AS book,
            br.borrower_name,
            br.roll_no,
            l.issue_date,
            l.due_date,
            l.return_date
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        JOIN borrowers br ON l.borrower_id = br.borrower_id
        ORDER BY l.loan_id DESC
    """)

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return records


@exports.route("/export/excel")
def excel():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    df = pd.DataFrame(get_loan_data())

    output = BytesIO()

    if df.empty:
        df = pd.DataFrame(columns=[
            "loan_id", "book", "borrower_name",
            "roll_no", "issue_date", "due_date", "return_date"
        ])

    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="library_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@exports.route("/export/pdf")
def pdf():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import landscape, A4

    records = get_loan_data()

    df = pd.DataFrame(records)

    if df.empty:
        df = pd.DataFrame(columns=[
            "loan_id", "book", "borrower_name",
            "roll_no", "issue_date", "due_date", "return_date"
        ])

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4)
    )

    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Library Management - Loan Report", styles["Title"]),
        Spacer(1, 15)
    ]

    rows = [list(df.columns)] + df.fillna("").astype(str).values.tolist()

    table = Table(rows, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 6)
    ]))

    elements.append(table)
    document.build(elements)

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="library_report.pdf",
        mimetype="application/pdf"
    )


@exports.route("/export/word")
def word():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    from docx import Document

    records = get_loan_data()

    df = pd.DataFrame(records)

    if df.empty:
        df = pd.DataFrame(columns=[
            "loan_id", "book", "borrower_name",
            "roll_no", "issue_date", "due_date", "return_date"
        ])

    output = BytesIO()

    doc = Document()

    doc.add_heading("Library Management - Loan Report", 0)

    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = "Table Grid"

    for i, column in enumerate(df.columns):
        table.rows[0].cells[i].text = str(column)

    for _, record in df.fillna("").iterrows():

        cells = table.add_row().cells

        for i, value in enumerate(record):
            cells[i].text = str(value)

    doc.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="library_report.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
