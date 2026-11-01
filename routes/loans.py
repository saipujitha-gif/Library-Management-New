
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import date, timedelta
from db import get_connection

loans = Blueprint("loans", __name__)


@loans.route("/loans", methods=["GET", "POST"])
def home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        book_id = request.form["book_id"]
        borrower_id = request.form["borrower_id"]

        issue_date = date.today()
        due_date = issue_date + timedelta(days=14)

        try:
            cursor.execute(
                """
                SELECT copies_available
                FROM books
                WHERE book_id = %s
                FOR UPDATE
                """,
                (book_id,)
            )

            book = cursor.fetchone()

            if not book or book["copies_available"] <= 0:

                flash("Book is not available.", "error")

            else:

                cursor.execute(
                    """
                    INSERT INTO loans
                    (book_id, borrower_id, issue_date, due_date)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (book_id, borrower_id, issue_date, due_date)
                )

                cursor.execute(
                    """
                    UPDATE books
                    SET copies_available = copies_available - 1
                    WHERE book_id = %s
                    """,
                    (book_id,)
                )

                conn.commit()

                flash("Book issued successfully!", "success")

        except Exception:
            conn.rollback()
            flash("Unable to issue book.", "error")

        cursor.close()
        conn.close()

        return redirect(url_for("loans.home"))

    cursor.execute(
        "SELECT * FROM books WHERE copies_available > 0"
    )
    book_list = cursor.fetchall()

    cursor.execute("SELECT * FROM borrowers")
    borrower_list = cursor.fetchall()

    cursor.execute(
        """
        SELECT l.*, b.title, br.borrower_name, br.roll_no
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        JOIN borrowers br ON l.borrower_id = br.borrower_id
        ORDER BY l.loan_id DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "loans.html",
        title="Issue and Return",
        book_list=book_list,
        borrower_list=borrower_list,
        records=records,
        today=date.today()
    )


@loans.route("/return/<int:loan_id>")
def return_book(loan_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT book_id, return_date
            FROM loans
            WHERE loan_id = %s
            FOR UPDATE
            """,
            (loan_id,)
        )

        loan = cursor.fetchone()

        if not loan:
            flash("Loan record not found.", "error")

        elif loan["return_date"]:
            flash("Book already returned.", "error")

        else:

            cursor.execute(
                """
                UPDATE loans
                SET return_date = %s
                WHERE loan_id = %s
                """,
                (date.today(), loan_id)
            )

            cursor.execute(
                """
                UPDATE books
                SET copies_available = copies_available + 1
                WHERE book_id = %s
                """,
                (loan["book_id"],)
            )

            conn.commit()

            flash("Book returned successfully!", "success")

    except Exception:
        conn.rollback()
        flash("Unable to return book.", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("loans.home"))
