from contextlib import closing

import pytest
import sqlite3 as sq
from sql_funcs import init_db, select_records
from book_funcs import validate_isbn, insert_book


@pytest.mark.parametrize("isbn, expected", [
    ("9780306406157", True),
    ("    9780306406157         ", False),
    ("9780306406158", False),
    ("12345", False),
    ("978030640615A", False),
    ("", False),
])
def test_isbn_validation(isbn, expected):
    assert validate_isbn(isbn) == expected


def test_double_isbn(test_db):
    init_db(test_db)
    book1 = {"isbn": "9780306406157",
            "name": "Преступление и наказание",
            "description": "Тварь я дрожащая, иль право имею?",
            "author": "Достоевский Фёдор Михайлович",
            "year": 1866,
            "publication_year": 2020,
            "path": test_db}

    book2 = {"isbn": "9780306406157",
            "name": "Преступление и наказание 2",
            "description": "Тварь я дрожащая, иль право имею? Вторая часть уже в продаже",
            "author": "Достоевский Фёдор Михайлович",
            "year": 1880,
            "publication_year": 2000,
            "path": test_db}

    insert_book(**book1)
    result = insert_book(**book2)

    with closing(sq.connect(test_db)) as conn:
        books = conn.execute("SELECT * FROM books").fetchall()

    assert result is False
    assert len(books) == 1
