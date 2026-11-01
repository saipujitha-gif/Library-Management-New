
from flask import Blueprint, render_template, session, redirect, url_for, flash
from db import get_connection

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
def home():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM books")
    books = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM borrowers")
    borrowers = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM loans WHERE return_date IS NULL"
    )
    issued = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COALESCE(SUM(copies_available), 0) AS total FROM books"
    )
    available = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM loans
        WHERE return_date IS NULL AND due_date < CURDATE()
        """
    )
    overdue = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        title="Dashboard",
        books=books,
        borrowers=borrowers,
        issued=issued,
        available=available,
        overdue=overdue
    )
