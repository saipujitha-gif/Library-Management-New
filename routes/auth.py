
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["full_name"].strip()
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("auth.register"))

        conn = get_connection()
        cursor = conn.cursor()

        try:
            hashed_password = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users
                (full_name, username, email, password)
                VALUES (%s, %s, %s, %s)
                """,
                (name, username, email, hashed_password)
            )

            conn.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("auth.login"))

        except Exception:
            conn.rollback()
            flash("Username or email already exists.", "error")

        finally:
            cursor.close()
            conn.close()

    return render_template("register.html", title="Register")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]

            return redirect(url_for("dashboard.home"))

        flash("Invalid username or password.", "error")

    return render_template("login.html", title="Login")


@auth.route("/logout")
def logout():

    session.clear()
    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))
