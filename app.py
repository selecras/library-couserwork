from flask import Flask, render_template, request, session, url_for, redirect, abort, g, flash
from functools import wraps
from datetime import datetime, timezone
import os
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from book_funcs import get_books, get_available_book_copies, insert_book, insert_phys_book
from user_funcs import login as authenticate_user, get_current_user
from loan_funcs import get_user_loans, validate_date, issue_book, return_book

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

csrf = CSRFProtect(app)


@app.before_request
def load_current_user():
    g.user = get_current_user(session)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.user is None:
            abort(401)  # Пользователь не прошел аутентификацию
        return func(*args, **kwargs)

    return wrapper


def librarian_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if g.user["role"] != "librarian":
            abort(403)
        return func(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    return render_template("index.html", library_name="Моя библиотека", user=g.user)


@app.route("/catalog")
def catalog():
    books = get_books(to_get=('name', 'author', 'year', 'book_id'))
    if books is not None:
        for book in books:
            copies = get_available_book_copies(book["book_id"])
            book['copies'] = len(copies) if copies is not None else 0
    return render_template("catalog.html", books=books)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username and password:
            user_id = authenticate_user(username, password)
            if user_id is not None:
                session.clear()
                session["user_id"] = user_id
                return redirect(url_for("profile"))
        return "Неверное имя пользователя или пароль"

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/profile")
@login_required
def profile():
    if g.user["role"] == "reader":
        loaned_books = get_user_loans(g.user["user_id"]) or {"loaned": [], "returned": []}
        if loaned_books is not None:
            now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
            for book in loaned_books.get("loaned", {}):
                due_at = validate_date(book["due_at"])
                if due_at is not None:
                    book["is_overdue"] = due_at < now
    else:
        loaned_books = {}
    return render_template(
        "profile.html",
        user=g.user,
        loaned_books=loaned_books
    )


@app.route("/librarian")
@librarian_required
def librarian_panel():
    return render_template("librarian.html")


@app.route("/librarian/issue_book", methods=["POST"])
@librarian_required
def issue_book_route():
    try:
        book_id = int(request.form.get("book_id", ))
        reader_id = int(request.form.get("reader_id"))
        due_at = datetime.fromisoformat(request.form.get("due_at", ""))
        due_at = due_at.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        flash("Некорректные данные формы", "error")
        return redirect(url_for("librarian_panel"))

    if book_id <= 0 or reader_id <= 0:
        flash("Некорректные данные формы", "error")
        return redirect(url_for("librarian_panel"))

    loan_id = issue_book(book_id, reader_id, g.user["user_id"], due_at)
    if loan_id is not None:
        flash(f"Книга успешно выдана! ID выдачи: {loan_id}", "success")
        return redirect(url_for("librarian_panel"))
    flash(f"Ошибка при выдаче", "error")
    return redirect(url_for("librarian_panel"))


@app.route("/librarian/return_book", methods=["POST"])
@librarian_required
def return_book_route():
    try:
        loan_id = int(request.form.get("loan_id"))
        if loan_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Некорректные данные формы", "error")
        return redirect(url_for("librarian_panel"))

    if return_book(loan_id, g.user["user_id"]):
        flash(f"Выдача с ID {loan_id} успешно возвращена", "success")
        return redirect(url_for("librarian_panel"))
    flash("Ошибка возврата", "error")
    return redirect(url_for("librarian_panel"))


@app.route("/librarian/add_book", methods=["POST"])
@librarian_required
def add_book_route():
    try:
        isbn = request.form.get("isbn").strip()
        name = request.form.get("name").strip()
        description = request.form.get("description").strip()
        author = request.form.get("author").strip()
        year_raw = request.form.get("year", "").strip()
        year = int(year_raw) if year_raw else None

        publication_year_raw = request.form.get("publication_year", "").strip()
        publication_year = int(publication_year_raw) if publication_year_raw else None

    except (ValueError, TypeError, AttributeError):
        flash("Некорректные данные формы", "error")
        return redirect(url_for("librarian_panel"))

    if (book_id := insert_book(isbn, name, description, author, year, publication_year)) is not None:
        flash(f"Книга успешно добавлена в каталог (ID = {book_id})", "success")
        return redirect(url_for("librarian_panel"))

    flash("Ошибка добавления книги", category="error")
    return redirect(url_for("librarian_panel"))


@app.route("/librarian/add_copy", methods=["POST"])
@librarian_required
def add_physical_copy_route():
    try:
        book_id = int(request.form.get("book_id_for_copy"))
        if book_id < 1:
            raise ValueError
    except (ValueError, TypeError):
        flash("Некорректные данные формы", "error")
        return redirect(url_for("librarian_panel"))

    if (phys_id := insert_phys_book(book_id)) is not None:
        flash(f"Успешно добавлен экзмепляр книги (ID = {phys_id})", category='success')
        return redirect(url_for("librarian_panel"))

    flash("Ошибка добавления экземпляра", category="error")
    return redirect(url_for("librarian_panel"))


