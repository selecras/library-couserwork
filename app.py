from flask import Flask, render_template, request, session, url_for, redirect, abort, g
from functools import wraps
import os
from book_funcs import get_books
from user_funcs import login as authenticate_user, get_current_user
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]


@app.before_request
def load_current_user():
    g.user = get_current_user(session)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.user is None:
            abort(401) # Пользователь не прошел аутентификацию
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
    return render_template(
        "index.html",
        library_name="Моя библиотека",
        user=g.user
    )


@app.route("/catalog")
def catalog():
    books = get_books()

    return render_template(
        "catalog.html",
        books=books
    )


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
    return render_template(
        "profile.html",
        user=g.user
    )


@app.route("/librarian")
@librarian_required
def librarian_panel():
    return "Панель библиотекаря"