
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_connection

borrowers = Blueprint("borrowers", __name__)


@borrowers.route("/borrowers", methods=["GET", "POST"])
def home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        name = request.form["name"].strip()
        roll = request.form["roll"].strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        try:
            cursor.execute(
                """
                INSERT INTO borrowers
                (borrower_name, roll_no, email, phone)
                VALUES (%s, %s, %s, %s)
                """,
                (name, roll, email, phone)
            )

            conn.commit()
            flash("Borrower added successfully!", "success")

        except Exception:
            conn.rollback()
            flash("Could not add borrower. Check the roll number.", "error")

        cursor.close()
        conn.close()

        return redirect(url_for("borrowers.home"))

    search = request.args.get("search", "")

    cursor.execute(
        """
        SELECT * FROM borrowers
        WHERE borrower_name LIKE %s OR roll_no LIKE %s
        ORDER BY borrower_id DESC
        """,
        (f"%{search}%", f"%{search}%")
    )

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "borrowers.html",
        title="Borrowers",
        records=records,
        search=search
    )


@borrowers.route("/borrower/delete/<int:borrower_id>")
def delete(borrower_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM borrowers WHERE borrower_id = %s",
            (borrower_id,)
        )

        conn.commit()
        flash("Borrower deleted successfully.", "success")

    except Exception:
        conn.rollback()
        flash("Cannot delete a borrower with loan records.", "error")

    cursor.close()
    conn.close()

    return redirect(url_for("borrowers.home"))
