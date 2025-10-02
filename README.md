# 📚 Library Management System (Flask + MySQL)

A simple yet powerful **Python-based Library Management System** built with **Flask** and **SQLAlchemy**, designed to manage books, users, issues, returns, and fines — all through a clean web-based admin panel.

This project is ideal for small libraries, educational institutions, or as a backend project to learn **Flask, SQLAlchemy, and MySQL integration**.

---

## 🚀 Features

✅ **Books Management** – Add, edit, delete, and view books with total and available copies tracking.  
✅ **User Management** – Register users, manage membership status, and edit user details.  
✅ **Issue & Return System** – Issue books, track due dates, process returns, and auto-calculate fines.  
✅ **Fine Calculation** – Automatically calculates overdue fines based on return date.  
✅ **Reports Dashboard** – Get insights into total books, users, active issues, overdue books, and fines collected.  
✅ **Admin Dashboard** – Simple web interface for all operations (no manual SQL needed).  
✅ **Seed Data & CLI Commands** – Quickly bootstrap sample data and create tables from the command line.

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL (via SQLAlchemy + PyMySQL)
- **ORM:** SQLAlchemy
- **Frontend:** HTML (rendered with Flask templates)

---

## 📁 Project Structure
```
.
├── library_management_system.py   # Main Flask app (single-file implementation)
├── README.md                      # Project documentation
└── requirements.txt               # Dependencies (optional)
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/library-management-system.git
cd library-management-system
```

### 2️⃣ Install Dependencies
```bash
pip install flask sqlalchemy pymysql
```

### 3️⃣ Configure Database
Create a MySQL database and user:
```sql
CREATE DATABASE library_db;
CREATE USER 'libuser'@'localhost' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON library_db.* TO 'libuser'@'localhost';
FLUSH PRIVILEGES;
```

Set your database URI (Linux/macOS):
```bash
export DATABASE_URI='mysql+pymysql://libuser:yourpassword@localhost/library_db'
```

Or edit the `DEFAULT_DB` variable in the code directly.

### 4️⃣ Initialize the Database
```bash
flask initdb
```

### 5️⃣ (Optional) Seed Sample Data
```bash
flask seed
```

### 6️⃣ Run the Application
```bash
python library_management_system.py
```
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 📊 Available CLI Commands
- `flask initdb` – Create all database tables
- `flask seed` – Add sample books and users for testing

---

## 📉 Future Improvements
- ✅ User authentication (admin login)
- ✅ Bulk upload via CSV
- ✅ Pagination and search
- ✅ REST API endpoints
- ✅ Email reminders for overdue books

---

## 🤝 Contributing
Feel free to fork, improve, and submit a PR. Contributions are welcome!

---

## 📜 License
MIT License © 2025 – Open Source Project

---

**Made with ❤️ in Python & Flask** – Designed for learning, scalability, and simplicity.
