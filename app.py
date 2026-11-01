
from flask import Flask, render_template, redirect, url_for, session, flash
from db import get_connection

from routes.auth import auth
from routes.dashboard import dashboard
from routes.books import books
from routes.borrowers import borrowers
from routes.loans import loans
from routes.reports import reports
from routes.exports import exports

app = Flask(__name__)

app.secret_key = "library-management-secret-key"

# Register all blueprints
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(books)
app.register_blueprint(borrowers)
app.register_blueprint(loans)
app.register_blueprint(reports)
app.register_blueprint(exports)


# Home page
@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard.home"))

    return redirect(url_for("auth.login"))


# Profile page
@app.route("/profile")
def profile():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT full_name, username, email, created_at
        FROM users
        WHERE user_id = %s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        title="Profile",
        user=user
    )


if __name__ == "__main__":
    app.run(debug=True)
