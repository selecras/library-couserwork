from flask import Flask, render_template, request
from book_funcs import get_books
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SERET_KEY"] = os.getenv("FLASK_SECRET_KEY")

@app.route("/")
def index():
    return render_template(
        "index.html",
        library_name="Моя библиотека"
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
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username.strip() and password:
            return "Данные получены"
        else:
            return "Заполните все поля"

    return render_template("login.html")
