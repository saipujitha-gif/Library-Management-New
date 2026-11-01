
# Library Management System

A web-based Library Management System developed using Python Flask and MySQL.

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS
- JavaScript
- Pandas
- NumPy
- Matplotlib

## Features

- User Registration and Login
- Dashboard with Library Statistics
- Book Management
- Borrower Management
- Issue and Return Books
- Automatic Due Date Calculation
- Overdue Book Tracking
- Reports and Analytics
- Category-wise Pie Chart
- Monthly Borrowing Chart
- Most Borrowed Books Chart
- Export Reports to Excel, PDF and Word
- User Profile

## Requirements

- Python 3.10 or above
- MySQL Server
- Visual Studio Code

## Installation and Execution

### 1. Download the Project

Clone the repository:

```bash
git clone https://github.com/saipujitha-gif/Library-Management-New.git
```

Open the downloaded folder in VS Code.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

### 4. Create the Database

Open MySQL Workbench.

Run all the commands from `database.sql`.

### 5. Configure Database Connection

Create a file named `.env` in the main project folder.

Add:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=library_management_new
DB_PORT=3306
```

Replace `your_mysql_password` with the MySQL password configured on that laptop.

### 6. Run the Application

Execute:

```bash
python app.py
```

### 7. Open the Application

Open your browser and visit:

http://127.0.0.1:5000

Create an account and log in to use the system.

## Project Structure

```text
Library-Management-New/
│
├── app.py
├── db.py
├── database.sql
├── requirements.txt
├── README.md
├── .gitignore
│
├── routes/
│   ├── auth.py
│   ├── dashboard.py
│   ├── books.py
│   ├── borrowers.py
│   ├── loans.py
│   ├── reports.py
│   └── exports.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── books.html
│   ├── borrowers.html
│   ├── loans.html
│   ├── reports.html
│   └── profile.html
│
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── script.js
    └── charts/
```

## Developed By

Library Management System Project
