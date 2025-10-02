"""
Single-file Flask Library Management System
- Uses SQLAlchemy with MySQL (pymysql) dialect
- Modules: Books, Users, Issues (borrowing), Returns, Fines
- Run: set DATABASE_URI environment variable or edit the default
- Dependencies: Flask, SQLAlchemy, pymysql

This is a simple, single-file administrative web app with HTML templates
rendered via render_template_string so you can run it without template files.
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Flask, request, redirect, url_for, render_template_string, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

# ----------------------- Configuration -----------------------
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-please-change')

# Example MySQL URI: mysql+pymysql://user:password@localhost/library_db
DEFAULT_DB = 'mysql+pymysql://root:password@localhost/library_db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', DEFAULT_DB)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------------- Models -----------------------
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=True)
    isbn = db.Column(db.String(50), nullable=True, unique=True)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Book {self.title} ({self.available_copies}/{self.total_copies})>"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=True, unique=True)
    membership_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    issues = relationship('Issue', back_populates='user')

    def __repr__(self):
        return f"<User {self.name} ({self.email})>"

class Issue(db.Model):
    __tablename__ = 'issues'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    fine_paid = db.Column(db.Numeric(10,2), default=0)

    user = relationship('User', back_populates='issues')
    book = relationship('Book')

    def is_overdue(self):
        if self.return_date:
            return self.return_date > self.due_date
        return datetime.utcnow() > self.due_date

    def current_fine(self, per_day=1.0):
        """Calculate fine in currency units per day overdue (default 1.0)."""
        per_day = Decimal(str(per_day))
        end = self.return_date or datetime.utcnow()
        overdue_days = (end.date() - self.due_date.date()).days
        if overdue_days > 0:
            return per_day * overdue_days
        return Decimal('0')

    def __repr__(self):
        return f"<Issue user={self.user_id} book={self.book_id} issued={self.issue_date}>"

# ----------------------- Utility / Setup -----------------------

@app.cli.command('initdb')
def initdb():
    """Create database tables."""
    db.create_all()
    print('Database tables created.')

# ----------------------- Views / Routes -----------------------

HOME_HTML = '''
<!doctype html>
<title>Library Admin</title>
<h1>Library Admin Dashboard</h1>
<p>
<a href="{{ url_for('list_books') }}">Books</a> |
<a href="{{ url_for('list_users') }}">Users</a> |
<a href="{{ url_for('list_issues') }}">Issues</a> |
<a href="{{ url_for('report') }}">Reports</a>
</p>
<hr>
<h3>Quick actions</h3>
<ul>
  <li><a href="{{ url_for('add_book') }}">Add book</a></li>
  <li><a href="{{ url_for('add_user') }}">Add user</a></li>
  <li><a href="{{ url_for('issue_book') }}">Issue a book</a></li>
</ul>
''' 

@app.route('/')
def home():
    stats = {
        'books': Book.query.count(),
        'users': User.query.count(),
        'active_issues': Issue.query.filter(Issue.return_date.is_(None)).count(),
    }
    return render_template_string(HOME_HTML + '<p>Books: {{stats.books}} | Users: {{stats.users}} | Active Issues: {{stats.active_issues}}</p>', stats=stats)

# ----------------------- Books -----------------------
BOOK_LIST_HTML = '''
<h2>Books</h2>
<a href="{{ url_for('home') }}">Back</a> | <a href="{{ url_for('add_book') }}">Add new</a>
<table border=1 cellpadding=6 cellspacing=0>
<tr><th>ID</th><th>Title</th><th>Author</th><th>ISBN</th><th>Available</th><th>Total</th><th>Actions</th></tr>
{% for b in books %}
<tr>
  <td>{{b.id}}</td>
  <td>{{b.title}}</td>
  <td>{{b.author}}</td>
  <td>{{b.isbn or ''}}</td>
  <td>{{b.available_copies}}</td>
  <td>{{b.total_copies}}</td>
  <td>
    <a href="{{ url_for('edit_book', book_id=b.id) }}">Edit</a> |
    <a href="{{ url_for('delete_book', book_id=b.id) }}" onclick="return confirm('Delete?')">Delete</a>
  </td>
</tr>
{% endfor %}
</table>
'''

@app.route('/books')
def list_books():
    books = Book.query.order_by(Book.title).all()
    return render_template_string(BOOK_LIST_HTML)

ADD_BOOK_HTML = '''
<h2>Add / Edit Book</h2>
<a href="{{ url_for('list_books') }}">Back to books</a>
<form method=post>
  Title: <input name=title value="{{book.title if book else ''}}" required><br>
  Author: <input name=author value="{{book.author if book else ''}}"><br>
  ISBN: <input name=isbn value="{{book.isbn if book else ''}}"><br>
  Total copies: <input name=total_copies type=number min=1 value="{{book.total_copies if book else 1}}"><br>
  <button type=submit>Save</button>
</form>
'''

@app.route('/books/add', methods=['GET', 'POST'])
@app.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
def add_book(book_id=None):
    book = Book.query.get(book_id) if book_id else None
    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form.get('author')
        isbn = request.form.get('isbn') or None
        total = int(request.form.get('total_copies') or 1)
        if book:
            book.title = title
            book.author = author
            # adjust available copies proportionally
            delta = total - book.total_copies
            book.total_copies = total
            book.available_copies = max(0, book.available_copies + delta)
            book.isbn = isbn
        else:
            book = Book(title=title, author=author, isbn=isbn, total_copies=total, available_copies=total)
            db.session.add(book)
        db.session.commit()
        flash('Book saved.')
        return redirect(url_for('list_books'))
    return render_template_string(ADD_BOOK_HTML, book=book)

@app.route('/books/<int:book_id>/delete')
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    # prevent delete when issued
    active_issue = Issue.query.filter_by(book_id=book.id, return_date=None).first()
    if active_issue:
        flash('Cannot delete: book is currently issued.')
        return redirect(url_for('list_books'))
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted.')
    return redirect(url_for('list_books'))

# ----------------------- Users -----------------------
USERS_LIST_HTML = '''
<h2>Users</h2>
<a href="{{ url_for('home') }}">Back</a> | <a href="{{ url_for('add_user') }}">Add new</a>
<table border=1 cellpadding=6 cellspacing=0>
<tr><th>ID</th><th>Name</th><th>Email</th><th>Active</th><th>Actions</th></tr>
{% for u in users %}
<tr>
  <td>{{u.id}}</td>
  <td>{{u.name}}</td>
  <td>{{u.email or ''}}</td>
  <td>{{'Yes' if u.is_active else 'No'}}</td>
  <td>
    <a href="{{ url_for('edit_user', user_id=u.id) }}">Edit</a> |
    <a href="{{ url_for('delete_user', user_id=u.id) }}" onclick="return confirm('Delete user?')">Delete</a>
  </td>
</tr>
{% endfor %}
</table>
'''

@app.route('/users')
def list_users():
    users = User.query.order_by(User.name).all()
    return render_template_string(USERS_LIST_HTML, users=users)

ADD_USER_HTML = '''
<h2>Add / Edit User</h2>
<a href="{{ url_for('list_users') }}">Back</a>
<form method=post>
  Name: <input name=name value="{{user.name if user else ''}}" required><br>
  Email: <input name=email value="{{user.email if user else ''}}"><br>
  Active: <input type=checkbox name=is_active {% if user and user.is_active %}checked{% endif %}><br>
  <button type=submit>Save</button>
</form>
'''

@app.route('/users/add', methods=['GET', 'POST'])
@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def add_user(user_id=None):
    user = User.query.get(user_id) if user_id else None
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form.get('email') or None
        is_active = bool(request.form.get('is_active'))
        if user:
            user.name = name
            user.email = email
            user.is_active = is_active
        else:
            user = User(name=name, email=email, is_active=is_active)
            db.session.add(user)
        db.session.commit()
        flash('User saved.')
        return redirect(url_for('list_users'))
    return render_template_string(ADD_USER_HTML, user=user)

@app.route('/users/<int:user_id>/delete')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    active_issue = Issue.query.filter_by(user_id=user.id, return_date=None).first()
    if active_issue:
        flash('Cannot delete: user has active issues.')
        return redirect(url_for('list_users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.')
    return redirect(url_for('list_users'))

# ----------------------- Issue / Return -----------------------
ISSUE_LIST_HTML = '''
<h2>Issues (Borrowings)</h2>
<a href="{{ url_for('home') }}">Back</a> | <a href="{{ url_for('issue_book') }}">Issue book</a>
<table border=1 cellpadding=6 cellspacing=0>
<tr><th>ID</th><th>User</th><th>Book</th><th>Issued</th><th>Due</th><th>Returned</th><th>Fine</th><th>Actions</th></tr>
{% for i in issues %}
<tr>
  <td>{{i.id}}</td>
  <td>{{i.user.name}}</td>
  <td>{{i.book.title}}</td>
  <td>{{i.issue_date.strftime('%Y-%m-%d')}}</td>
  <td>{{i.due_date.strftime('%Y-%m-%d')}}</td>
  <td>{{i.return_date.strftime('%Y-%m-%d') if i.return_date else '-'}}</td>
  <td>{{ i.current_fine() }}</td>
  <td>
    {% if not i.return_date %}
      <a href="{{ url_for('return_book', issue_id=i.id) }}">Return</a>
    {% else %}
      <small>Closed</small>
    {% endif %}
  </td>
</tr>
{% endfor %}
</table>
'''

ISSUE_BOOK_HTML = '''
<h2>Issue a Book</h2>
<a href="{{ url_for('list_issues') }}">Back to issues</a>
<form method=post>
  User: <select name=user_id required>
    {% for u in users %}
    <option value="{{u.id}}">{{u.name}} ({{u.email or 'no-email'}})</option>
    {% endfor %}
  </select><br>
  Book: <select name=book_id required>
    {% for b in books %}
    <option value="{{b.id}}">{{b.title}} (Avail: {{b.available_copies}})</option>
    {% endfor %}
  </select><br>
  Days to borrow: <input name=days type=number min=1 value=14><br>
  <button type=submit>Issue</button>
</form>
'''

@app.route('/issues')
def list_issues():
    issues = Issue.query.order_by(Issue.issue_date.desc()).all()
    return render_template_string(ISSUE_LIST_HTML, issues=issues)

@app.route('/issues/issue', methods=['GET', 'POST'])
def issue_book():
    users = User.query.filter_by(is_active=True).all()
    books = Book.query.filter(Book.available_copies > 0).all()
    if request.method == 'POST':
        user_id = int(request.form['user_id'])
        book_id = int(request.form['book_id'])
        days = int(request.form.get('days') or 14)
        user = User.query.get_or_404(user_id)
        book = Book.query.get_or_404(book_id)
        if book.available_copies <= 0:
            flash('Book not available')
            return redirect(url_for('issue_book'))
        issue = Issue(user_id=user.id, book_id=book.id, issue_date=datetime.utcnow(), due_date=datetime.utcnow() + timedelta(days=days))
        book.available_copies -= 1
        db.session.add(issue)
        db.session.commit()
        flash('Book issued successfully')
        return redirect(url_for('list_issues'))
    return render_template_string(ISSUE_BOOK_HTML, users=users, books=books)

RETURN_HTML = '''
<h2>Return Book</h2>
<p>User: {{issue.user.name}} | Book: {{issue.book.title}}</p>
<p>Issued: {{issue.issue_date.strftime('%Y-%m-%d')}} | Due: {{issue.due_date.strftime('%Y-%m-%d')}}</p>
<form method=post>
  Return date (YYYY-MM-DD, leave blank for today): <input name=return_date><br>
  Fine paid (numeric, leave blank to auto-calc): <input name=fine_paid><br>
  <button type=submit>Process Return</button>
</form>
'''

@app.route('/issues/<int:issue_id>/return', methods=['GET', 'POST'])
def return_book(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    if issue.return_date:
        flash('Already returned')
        return redirect(url_for('list_issues'))
    if request.method == 'POST':
        raw_date = request.form.get('return_date')
        if raw_date:
            return_date = datetime.strptime(raw_date.strip(), '%Y-%m-%d')
        else:
            return_date = datetime.utcnow()
        issue.return_date = return_date
        auto_fine = issue.current_fine(per_day=1.0)
        raw_fine = request.form.get('fine_paid')
        if raw_fine:
            paid = Decimal(raw_fine)
        else:
            paid = auto_fine
        issue.fine_paid = paid
        # increment available copies
        issue.book.available_copies = min(issue.book.total_copies, issue.book.available_copies + 1)
        db.session.commit()
        flash(f'Returned. Fine recorded: {paid}')
        return redirect(url_for('list_issues'))
    return render_template_string(RETURN_HTML, issue=issue)

# ----------------------- Reports -----------------------
REPORT_HTML = '''
<h2>Reports</h2>
<a href="{{ url_for('home') }}">Back</a>
<ul>
<li>Total books: {{books_count}}</li>
<li>Total users: {{users_count}}</li>
<li>Active issues: {{active_issues}}</li>
<li>Overdue items: {{overdue}}</li>
<li>Total fines outstanding: {{total_fines}}</li>
</ul>
'''

@app.route('/reports')
def report():
    books_count = Book.query.count()
    users_count = User.query.count()
    active_issues = Issue.query.filter(Issue.return_date.is_(None)).count()
    overdue_q = [i for i in Issue.query.filter(Issue.return_date.is_(None)).all() if i.is_overdue()]
    overdue = len(overdue_q)
    # total fines (sum of recorded fines)
    total_fines = sum([float(i.fine_paid or 0) for i in Issue.query.all()])
    return render_template_string(REPORT_HTML, books_count=books_count, users_count=users_count, active_issues=active_issues, overdue=overdue, total_fines=total_fines)

# ----------------------- Sample Data Loader -----------------------
@app.cli.command('seed')
def seed():
    """Add sample data (for quick testing)."""
    db.create_all()
    if Book.query.count() == 0:
        sample_books = [
            Book(title='Clean Code', author='Robert C. Martin', isbn='9780132350884', total_copies=3, available_copies=3),
            Book(title='Introduction to Algorithms', author='Cormen et al', isbn='9780262033848', total_copies=2, available_copies=2),
            Book(title='Design Patterns', author='Gamma et al', isbn='9780201633610', total_copies=2, available_copies=2),
        ]
        db.session.add_all(sample_books)
    if User.query.count() == 0:
        sample_users = [
            User(name='Alice'),
            User(name='Bob'),
            User(name='Charlie'),
        ]
        db.session.add_all(sample_users)
    db.session.commit()
    print('Seeded sample data.')

# ----------------------- Run -----------------------
if __name__ == '__main__':
    # for testing convenience only; use gunicorn/uvicorn in production
    app.run(debug=True)
