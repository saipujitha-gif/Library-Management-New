
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_connection

books = Blueprint("books", __name__)


@books.route("/books", methods=["GET", "POST"])
def home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        isbn = request.form.get("isbn", "").strip() or None
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        category = request.form.get("category", "").strip()
        copies = int(request.form["copies"])

        if copies < 1:
            flash("Copies must be at least 1.", "error")

        else:
            try:
                cursor.execute(
                    """
                    INSERT INTO books
                    (isbn, title, author, category,
                     total_copies, copies_available)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (isbn, title, author, category, copies, copies)
                )

                conn.commit()
                flash("Book added successfully!", "success")

            except Exception:
                conn.rollback()
                flash("Could not add book. Check the ISBN.", "error")

        cursor.close()
        conn.close()

        return redirect(url_for("books.home"))

    search = request.args.get("search", "")

    cursor.execute(
        """
        SELECT * FROM books
        WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s
        ORDER BY book_id DESC
        """,
        (f"%{search}%", f"%{search}%", f"%{search}%")
    )

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "books.html",
        title="Books",
        records=records,
        search=search
    )


@books.route("/book/delete/<int:book_id>")
def delete(book_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM books WHERE book_id = %s",
            (book_id,)
        )

        conn.commit()
        flash("Book deleted successfully.", "success")

    except Exception:
        conn.rollback()
        flash("Cannot delete a book with loan records.", "error")

    cursor.close()
    conn.close()

    return redirect(url_for("books.home"))
