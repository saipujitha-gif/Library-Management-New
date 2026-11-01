
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from db import get_connection
from datetime import date, timedelta
from io import BytesIO
import pandas as pd

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-secret"

# ---------- DATABASE HELPERS ----------

def fetch_all(sql, values=()):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, values)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def execute(sql, values=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper

# ---------- COMMON PAGE DESIGN ----------

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>{{ title }} - Library Management</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {box-sizing:border-box}
body {margin:0;font-family:Arial,sans-serif;background:white;color:#263445}
header {background:#17365D;color:white;padding:18px 28px;display:flex;
justify-content:space-between;align-items:center}
header h2 {margin:0;font-size:21px}
nav {background:#17365D;padding:0 28px 16px;display:flex;gap:20px;flex-wrap:wrap}
nav a {color:white;text-decoration:none;font-size:14px}
nav a:hover {text-decoration:underline}
main {padding:25px;max-width:1250px;margin:auto}
h2,h3 {color:#17365D}
.card {border:1px solid #d7dce3;padding:18px;background:white;margin-bottom:18px}
.stats {display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px}
.stat {border:1px solid #17365D;padding:18px}
.stat h2 {font-size:27px;margin:8px 0}
input,select {padding:10px;width:100%;border:1px solid #aaa;margin:6px 0 14px}
button,.btn {background:#17365D;color:white;border:0;padding:10px 16px;
cursor:pointer;text-decoration:none;display:inline-block}
button:hover,.btn:hover {background:#254d7d}
table {width:100%;border-collapse:collapse;margin-top:12px}
th,td {padding:11px;border:1px solid #ddd;text-align:left;font-size:14px}
th {background:#17365D;color:white}
.success {color:#16803c;background:#eaf6ed;padding:10px;margin:10px 0}
.error {color:#c62828;background:#fdecec;padding:10px;margin:10px 0}
.actions {display:flex;gap:8px;flex-wrap:wrap}
form.inline {display:inline}
small {color:#666}
@media(max-width:600px){main{padding:14px}header{padding:15px}nav{padding:0 15px 15px}}
</style>
</head>
<body>
<header>
<h2>Library Management System</h2>
{% if session.get('user_id') %}
<span>{{ session.get('full_name') }}</span>
{% endif %}
</header>
{% if session.get('user_id') %}
<nav>
<a href="{{ url_for('dashboard') }}">Dashboard</a>
<a href="{{ url_for('books') }}">Books</a>
<a href="{{ url_for('borrowers') }}">Borrowers</a>
<a href="{{ url_for('loans') }}">Issue / Return</a>
<a href="{{ url_for('reports') }}">Reports</a>
<a href="{{ url_for('profile') }}">Profile</a>
<a href="{{ url_for('logout') }}">Logout</a>
</nav>
{% endif %}
<main>
{% for category,message in get_flashed_messages(with_categories=true) %}
<div class="{{ category }}">{{ message }}</div>
{% endfor %}
{{ body|safe }}
</main>
</body>
</html>
"""

def page(title, template, **data):
    body = render_template_string(template, **data)
    return render_template_string(BASE, title=title, body=body)

# ---------- REGISTRATION ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["full_name"].strip()
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not all([name, username, email, password]):
            flash("Please fill in every field.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        else:
            try:
                execute(
                    "INSERT INTO users(full_name,username,email,password) VALUES(%s,%s,%s,%s)",
                    (name, username, email, generate_password_hash(password))
                )
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("login"))
            except Exception:
                flash("Username or email may already be registered.", "error")

    return page("Register", """
    <div class="card" style="max-width:450px;margin:35px auto">
    <h2>Create Account</h2>
    <form method="POST">
    Full Name<input name="full_name" required>
    Username<input name="username" required>
    Email<input type="email" name="email" required>
    Password<input type="password" name="password" minlength="8" required>
    <button type="submit">Register</button>
    </form>
    <p>Already registered? <a href="/login">Login</a></p>
    </div>
    """)

# ---------- LOGIN AND LOGOUT ----------

@app.route("/", methods=["GET"])
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        users = fetch_all("SELECT * FROM users WHERE username=%s", (username,))

        if users and check_password_hash(users[0]["password"], password):
            session["user_id"] = users[0]["user_id"]
            session["full_name"] = users[0]["full_name"]
            return redirect(url_for("dashboard"))

        flash("Incorrect username or password.", "error")

    return page("Login", """
    <div class="card" style="max-width:420px;margin:45px auto">
    <h2>Login</h2>
    <form method="POST">
    Username<input name="username" required>
    Password<input type="password" name="password" required>
    <button type="submit">Login</button>
    </form>
    <p>New user? <a href="/register">Create an account</a></p>
    </div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("login"))

# ---------- DASHBOARD ----------

@app.route("/dashboard")
@login_required
def dashboard():
    books = fetch_all("SELECT COUNT(*) AS total FROM books")[0]["total"]
    borrowers = fetch_all("SELECT COUNT(*) AS total FROM borrowers")[0]["total"]
    issued = fetch_all("SELECT COUNT(*) AS total FROM loans WHERE return_date IS NULL")[0]["total"]
    available = fetch_all("SELECT COALESCE(SUM(copies_available),0) AS total FROM books")[0]["total"]
    overdue = fetch_all(
        "SELECT COUNT(*) AS total FROM loans WHERE return_date IS NULL AND due_date < CURDATE()"
    )[0]["total"]

    return page("Dashboard", """
    <h2>Dashboard</h2>
    <p>Library overview</p>
    <div class="stats">
    <div class="stat">Total Books<h2>{{ books }}</h2></div>
    <div class="stat">Borrowers<h2>{{ borrowers }}</h2></div>
    <div class="stat">Books Issued<h2>{{ issued }}</h2></div>
    <div class="stat">Available Copies<h2>{{ available }}</h2></div>
    <div class="stat">Overdue Books<h2>{{ overdue }}</h2></div>
    </div>
    """, books=books, borrowers=borrowers, issued=issued,
    available=available, overdue=overdue)

# ---------- BOOK MANAGEMENT ----------

@app.route("/books", methods=["GET", "POST"])
@login_required
def books():
    if request.method == "POST":
        isbn = request.form["isbn"].strip() or None
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        category = request.form["category"].strip()
        copies = int(request.form["copies"])

        if copies < 1:
            flash("Copies must be at least 1.", "error")
        else:
            try:
                execute(
                    """INSERT INTO books(isbn,title,author,category,total_copies,copies_available)
                    VALUES(%s,%s,%s,%s,%s,%s)""",
                    (isbn,title,author,category,copies,copies)
                )
                flash("Book successfully registered!", "success")
            except Exception:
                flash("Book could not be registered. Check the ISBN.", "error")

        return redirect(url_for("books"))

    search = request.args.get("search", "")
    records = fetch_all(
        """SELECT * FROM books
        WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s
        ORDER BY book_id DESC""",
        (f"%{search}%",f"%{search}%",f"%{search}%")
    )

    return page("Books", """
    <h2>Book Management</h2>
    <div class="card">
    <h3>Register New Book</h3>
    <form method="POST">
    ISBN<input name="isbn">
    Title<input name="title" required>
    Author<input name="author" required>
    Category<input name="category">
    Total Copies<input type="number" name="copies" min="1" value="1" required>
    <button>Register Book</button>
    </form>
    </div>
    <form method="GET">
    <input name="search" placeholder="Search title, author or ISBN" value="{{ search }}">
    <button>Search</button>
    </form>
    <h3>Book List</h3>
    <table><tr><th>ID</th><th>ISBN</th><th>Title</th><th>Author</th>
    <th>Category</th><th>Total</th><th>Available</th><th>Action</th></tr>
    {% for b in records %}
    <tr><td>{{ b.book_id }}</td><td>{{ b.isbn or '-' }}</td>
    <td>{{ b.title }}</td><td>{{ b.author }}</td><td>{{ b.category or '-' }}</td>
    <td>{{ b.total_copies }}</td><td>{{ b.copies_available }}</td>
    <td><a href="/book/delete/{{ b.book_id }}">Delete</a></td></tr>
    {% endfor %}</table>
    """, records=records, search=search)

@app.route("/book/delete/<int:book_id>")
@login_required
def delete_book(book_id):
    try:
        execute("DELETE FROM books WHERE book_id=%s", (book_id,))
        flash("Book deleted successfully.", "success")
    except Exception:
        flash("Cannot delete a book with existing loan records.", "error")
    return redirect(url_for("books"))

# ---------- BORROWER MANAGEMENT ----------

@app.route("/borrowers", methods=["GET", "POST"])
@login_required
def borrowers():
    if request.method == "POST":
        name = request.form["name"].strip()
        roll = request.form["roll"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()

        try:
            execute(
                """INSERT INTO borrowers(borrower_name,roll_no,email,phone)
                VALUES(%s,%s,%s,%s)""",
                (name,roll,email,phone)
            )
            flash("Borrower successfully registered!", "success")
        except Exception:
            flash("Borrower could not be registered. Check the roll number.", "error")

        return redirect(url_for("borrowers"))

    search = request.args.get("search", "")
    records = fetch_all(
        """SELECT * FROM borrowers
        WHERE borrower_name LIKE %s OR roll_no LIKE %s
        ORDER BY borrower_id DESC""",
        (f"%{search}%",f"%{search}%")
    )

    return page("Borrowers", """
    <h2>Borrower Management</h2>
    <div class="card">
    <h3>Register Borrower</h3>
    <form method="POST">
    Name<input name="name" required>
    Roll Number<input name="roll" required>
    Email<input type="email" name="email">
    Phone<input name="phone">
    <button>Register Borrower</button>
    </form>
    </div>
    <form method="GET">
    <input name="search" placeholder="Search name or roll number" value="{{ search }}">
    <button>Search</button>
    </form>
    <table><tr><th>ID</th><th>Name</th><th>Roll Number</th><th>Email</th><th>Phone</th><th>Action</th></tr>
    {% for b in records %}
    <tr><td>{{ b.borrower_id }}</td><td>{{ b.borrower_name }}</td>
    <td>{{ b.roll_no }}</td><td>{{ b.email or '-' }}</td><td>{{ b.phone or '-' }}</td>
    <td><a href="/borrower/delete/{{ b.borrower_id }}">Delete</a></td></tr>
    {% endfor %}</table>
    """, records=records, search=search)

@app.route("/borrower/delete/<int:borrower_id>")
@login_required
def delete_borrower(borrower_id):
    try:
        execute("DELETE FROM borrowers WHERE borrower_id=%s", (borrower_id,))
        flash("Borrower deleted successfully.", "success")
    except Exception:
        flash("Cannot delete a borrower with existing loan records.", "error")
    return redirect(url_for("borrowers"))

# ---------- ISSUE AND RETURN ----------

@app.route("/loans", methods=["GET", "POST"])
@login_required
def loans():
    if request.method == "POST":
        book_id = int(request.form["book_id"])
        borrower_id = int(request.form["borrower_id"])
        issue_date = date.today()
        due_date = issue_date + timedelta(days=14)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT copies_available FROM books WHERE book_id=%s FOR UPDATE",
                (book_id,)
            )
            book = cursor.fetchone()

            if not book or book["copies_available"] <= 0:
                flash("This book is not currently available.", "error")
            else:
                cursor.execute(
                    """INSERT INTO loans(book_id,borrower_id,issue_date,due_date)
                    VALUES(%s,%s,%s,%s)""",
                    (book_id,borrower_id,issue_date,due_date)
                )
                cursor.execute(
                    "UPDATE books SET copies_available=copies_available-1 WHERE book_id=%s",
                    (book_id,)
                )
                conn.commit()
                flash("Book issued successfully!", "success")

        except Exception:
            conn.rollback()
            flash("Could not issue the book. Check the selected records.", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("loans"))

    book_list = fetch_all("SELECT * FROM books WHERE copies_available > 0")
    borrower_list = fetch_all("SELECT * FROM borrowers")
    records = fetch_all("""
        SELECT l.*,b.title,br.borrower_name,br.roll_no
        FROM loans l
        JOIN books b ON l.book_id=b.book_id
        JOIN borrowers br ON l.borrower_id=br.borrower_id
        ORDER BY l.loan_id DESC
    """)

    return page("Issue and Return", """
    <h2>Issue and Return Books</h2>
    <div class="card">
    <h3>Issue a Book (14-day loan period)</h3>
    <form method="POST">
    Select Book<select name="book_id" required>
    {% for b in book_list %}
    <option value="{{ b.book_id }}">{{ b.title }} ({{ b.copies_available }} available)</option>
    {% endfor %}</select>
    Select Borrower<select name="borrower_id" required>
    {% for b in borrower_list %}
    <option value="{{ b.borrower_id }}">{{ b.borrower_name }} - {{ b.roll_no }}</option>
    {% endfor %}</select>
    <button {% if not book_list or not borrower_list %}disabled{% endif %}>Issue Book</button>
    </form>
    </div>
    <h3>Loan Records</h3>
    <table><tr><th>ID</th><th>Book</th><th>Borrower</th><th>Issue Date</th>
    <th>Due Date</th><th>Status</th><th>Action</th></tr>
    {% for l in records %}
    <tr><td>{{ l.loan_id }}</td><td>{{ l.title }}</td>
    <td>{{ l.borrower_name }} ({{ l.roll_no }})</td>
    <td>{{ l.issue_date }}</td><td>{{ l.due_date }}</td>
    <td>{% if l.return_date %}Returned{% elif l.due_date|string < today %}Overdue{% else %}Issued{% endif %}</td>
    <td>{% if not l.return_date %}
    <a href="/return/{{ l.loan_id }}">Return Book</a>
    {% else %}-{% endif %}</td></tr>
    {% endfor %}</table>
    """, book_list=book_list, borrower_list=borrower_list,
    records=records, today=str(date.today()))

@app.route("/return/<int:loan_id>")
@login_required
def return_book(loan_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT book_id,return_date FROM loans WHERE loan_id=%s FOR UPDATE",
            (loan_id,)
        )
        loan = cursor.fetchone()

        if not loan:
            flash("Loan record not found.", "error")
        elif loan["return_date"]:
            flash("This book has already been returned.", "error")
        else:
            cursor.execute(
                "UPDATE loans SET return_date=%s WHERE loan_id=%s",
                (date.today(),loan_id)
            )
            cursor.execute(
                "UPDATE books SET copies_available=copies_available+1 WHERE book_id=%s",
                (loan["book_id"],)
            )
            conn.commit()
            flash("Book returned successfully!", "success")

    except Exception:
        conn.rollback()
        flash("Unable to return the book.", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("loans"))

# ---------- REPORTS ----------

@app.route("/reports")
@login_required
def reports():
    most = fetch_all("""
        SELECT b.title,COUNT(l.loan_id) AS total
        FROM books b LEFT JOIN loans l ON b.book_id=l.book_id
        GROUP BY b.book_id,b.title ORDER BY total DESC LIMIT 10
    """)

    overdue = fetch_all("""
        SELECT b.title,br.borrower_name,br.roll_no,l.due_date
        FROM loans l JOIN books b ON l.book_id=b.book_id
        JOIN borrowers br ON l.borrower_id=br.borrower_id
        WHERE l.return_date IS NULL AND l.due_date < CURDATE()
    """)

    categories = fetch_all("""
        SELECT category,COUNT(*) AS total FROM books
        GROUP BY category ORDER BY total DESC
    """)

    monthly = fetch_all("""
        SELECT DATE_FORMAT(issue_date,'%Y-%m') AS month,
        COUNT(*) AS total FROM loans
        GROUP BY DATE_FORMAT(issue_date,'%Y-%m')
        ORDER BY month DESC LIMIT 12
    """)

    return page("Reports", """
    <h2>Reports and Analytics</h2>
    <p>Export the loan records using the options below.</p>
    <div class="actions">
    <a class="btn" href="/export/excel">Export Excel</a>
    <a class="btn" href="/export/pdf">Export PDF</a>
    <a class="btn" href="/export/word">Export Word</a>
    </div>
    <h3>Most Borrowed Books</h3>
    <table><tr><th>Book</th><th>Times Borrowed</th></tr>
    {% for x in most %}<tr><td>{{ x.title }}</td><td>{{ x.total }}</td></tr>{% endfor %}</table>
    <h3>Category Statistics</h3>
    <table><tr><th>Category</th><th>Number of Books</th></tr>
    {% for x in categories %}<tr><td>{{ x.category or 'Uncategorized' }}</td><td>{{ x.total }}</td></tr>{% endfor %}</table>
    <h3>Monthly Issue Trends</h3>
    <table><tr><th>Month</th><th>Books Issued</th></tr>
    {% for x in monthly %}<tr><td>{{ x.month }}</td><td>{{ x.total }}</td></tr>{% endfor %}</table>
    <h3>Overdue Books</h3>
    <table><tr><th>Book</th><th>Borrower</th><th>Roll Number</th><th>Due Date</th></tr>
    {% for x in overdue %}
    <tr><td>{{ x.title }}</td><td>{{ x.borrower_name }}</td>
    <td>{{ x.roll_no }}</td><td>{{ x.due_date }}</td></tr>
    {% endfor %}</table>
    """, most=most, categories=categories, monthly=monthly, overdue=overdue)

# ---------- EXPORTS ----------

def get_export_data():
    return fetch_all("""
        SELECT l.loan_id,b.title AS book,br.borrower_name,br.roll_no,
        l.issue_date,l.due_date,l.return_date
        FROM loans l JOIN books b ON l.book_id=b.book_id
        JOIN borrowers br ON l.borrower_id=br.borrower_id
        ORDER BY l.loan_id DESC
    """)

@app.route("/export/<kind>")
@login_required
def export(kind):
    data = get_export_data()
    df = pd.DataFrame(data)

    if df.empty:
        df = pd.DataFrame(columns=[
            "loan_id","book","borrower_name","roll_no",
            "issue_date","due_date","return_date"
        ])

    output = BytesIO()

    if kind == "excel":
        df.to_excel(output,index=False)
        filename = "library_report.xlsx"
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    elif kind == "pdf":
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.pagesizes import landscape, A4

        document = SimpleDocTemplate(output,pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("Library Management - Loan Report",styles["Title"]),
            Spacer(1,15)
        ]
        rows = [list(df.columns)] + df.fillna("").astype(str).values.tolist()
        table = Table(rows,repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365D")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
            ("FONTSIZE",(0,0),(-1,-1),8),
            ("PADDING",(0,0),(-1,-1),6)
        ]))
        elements.append(table)
        document.build(elements)
        filename = "library_report.pdf"
        mimetype = "application/pdf"

    elif kind == "word":
        from docx import Document
        doc = Document()
        doc.add_heading("Library Management - Loan Report",0)
        table = doc.add_table(rows=1,cols=len(df.columns))
        table.style = "Table Grid"
        for i,col in enumerate(df.columns):
            table.rows[0].cells[i].text = str(col)
        for _,record in df.fillna("").iterrows():
            cells = table.add_row().cells
            for i,value in enumerate(record):
                cells[i].text = str(value)
        doc.save(output)
        filename = "library_report.docx"
        mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    else:
        return "Invalid export format",400

    output.seek(0)
    return send_file(output,as_attachment=True,download_name=filename,mimetype=mimetype)

# ---------- PROFILE ----------

@app.route("/profile")
@login_required
def profile():
    user = fetch_all(
        "SELECT full_name,username,email,created_at FROM users WHERE user_id=%s",
        (session["user_id"],)
    )[0]

    return page("Profile", """
    <h2>My Profile</h2>
    <div class="card">
    <p><b>Name:</b> {{ user.full_name }}</p>
    <p><b>Username:</b> {{ user.username }}</p>
    <p><b>Email:</b> {{ user.email }}</p>
    <p><b>Registered:</b> {{ user.created_at }}</p>
    <a class="btn" href="/logout">Logout</a>
    </div>
    """, user=user)

if __name__ == "__main__":
    app.run(debug=True)
