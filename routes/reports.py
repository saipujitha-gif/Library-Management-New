
from flask import Blueprint, render_template, redirect, url_for, session, flash
from db import get_connection
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

reports = Blueprint("reports", __name__)

CHART_FOLDER = os.path.join("static", "charts")
os.makedirs(CHART_FOLDER, exist_ok=True)


def get_data(sql):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(sql)
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def create_charts():

    # 1. CATEGORY PIE CHART

    categories = get_data("""
        SELECT COALESCE(category, 'Uncategorized') AS category,
        COUNT(*) AS total
        FROM books
        GROUP BY category
    """)

    plt.figure(figsize=(7, 5))

    if categories:
        labels = [x["category"] for x in categories]
        values = [x["total"] for x in categories]

        plt.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90
        )
    else:
        plt.text(0.5, 0.5, "No book data available",
                 ha="center", va="center")

    plt.title("Books by Category")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, "category_pie.png"))
    plt.close()


    # 2. MONTHLY BORROWING BAR CHART

    monthly = get_data("""
        SELECT DATE_FORMAT(issue_date, '%Y-%m') AS month,
        COUNT(*) AS total
        FROM loans
        GROUP BY DATE_FORMAT(issue_date, '%Y-%m')
        ORDER BY month
    """)

    plt.figure(figsize=(8, 5))

    if monthly:
        months = [x["month"] for x in monthly]
        totals = [x["total"] for x in monthly]

        plt.bar(months, totals)
        plt.xlabel("Month")
        plt.ylabel("Number of Books Issued")
        plt.xticks(rotation=45)
    else:
        plt.text(0.5, 0.5, "No borrowing data available",
                 ha="center", va="center")

    plt.title("Monthly Borrowing Trends")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, "monthly_trend.png"))
    plt.close()


    # 3. MOST BORROWED BOOKS BAR CHART

    most = get_data("""
        SELECT b.title, COUNT(l.loan_id) AS total
        FROM books b
        JOIN loans l ON b.book_id = l.book_id
        GROUP BY b.book_id, b.title
        ORDER BY total DESC
        LIMIT 10
    """)

    plt.figure(figsize=(8, 5))

    if most:
        titles = [x["title"] for x in most]
        totals = [x["total"] for x in most]

        plt.barh(titles[::-1], totals[::-1])
        plt.xlabel("Times Borrowed")
    else:
        plt.text(0.5, 0.5, "No borrowing data available",
                 ha="center", va="center")

    plt.title("Most Borrowed Books")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, "most_borrowed.png"))
    plt.close()


@reports.route("/reports")
def home():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    categories = get_data("""
        SELECT COALESCE(category, 'Uncategorized') AS category,
        COUNT(*) AS total
        FROM books
        GROUP BY category
    """)

    most = get_data("""
        SELECT b.title, COUNT(l.loan_id) AS total
        FROM books b
        JOIN loans l ON b.book_id = l.book_id
        GROUP BY b.book_id, b.title
        ORDER BY total DESC
        LIMIT 10
    """)

    monthly = get_data("""
        SELECT DATE_FORMAT(issue_date, '%Y-%m') AS month,
        COUNT(*) AS total
        FROM loans
        GROUP BY DATE_FORMAT(issue_date, '%Y-%m')
        ORDER BY month DESC
        LIMIT 12
    """)

    overdue = get_data("""
        SELECT b.title, br.borrower_name,
        br.roll_no, l.due_date
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        JOIN borrowers br ON l.borrower_id = br.borrower_id
        WHERE l.return_date IS NULL
        AND l.due_date < CURDATE()
    """)

    create_charts()

    return render_template(
        "reports.html",
        title="Reports",
        categories=categories,
        most=most,
        monthly=monthly,
        overdue=overdue
    )
