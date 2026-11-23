from datetime import datetime
from contextlib import closing
import sqlite3 as sq
from sql_funcs import insert_any_sql, PATH


def validate_isbn(isbn: str) -> bool:
    if len(isbn) != 13:
        return False
    if not all(i in "1234567890" for i in isbn):
        return False

    checksum = sum(int(num) * int("13"[i % 2]) for i, num in enumerate(isbn[:-1]))
    check13 = (10 - (checksum % 10)) % 10

    if isbn[-1] != str(check13):
        return False
    return True


def insert_book(
    isbn: str,
    name: str,
    description: str = "",
    author: str = "",
    year: int | None = None,
    publication_year: int | None = None,
    path: str = PATH,
) -> bool:

    if year is not None:
        if not (-5000 <= year <= datetime.now().year):
            return False

    if publication_year is not None:
        if not (-5000 <= publication_year <= datetime.now().year):
            return False

    if year is not None and publication_year is not None:
        if publication_year < year:
            return False

    isbn = isbn.strip()
    if not validate_isbn(isbn):
        return False

    return insert_any_sql(
        ("name", "description", "author", "year", "publication_year", "isbn"),
        (name, description, author, year, publication_year, isbn),
        "books",
        path,
    )


def insert_phys_book(book_id: int, path: str = PATH) -> bool:
    return insert_any_sql(("book_id",), (book_id,), "book_copies", path)


def get_books(
    path: str = PATH, to_get: tuple | list = ("name", "author", "year")
) -> list[sq.Row] | None:
    whitelist = (
        "book_id",
        "name",
        "description",
        "author",
        "year",
        "publication_year",
        "added_at",
        "isbn",
    )
    if not to_get or not all(i in whitelist for i in to_get):
        return None

    try:
        with closing(sq.connect(path)) as conn:
            conn.row_factory = sq.Row

            data = conn.execute(f"""
            SELECT {", ".join(to_get)}
            FROM books;
            """).fetchall()
    except sq.Error as e:
        print(f"[ERROR] {e}")
        return None

    return data
