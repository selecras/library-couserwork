import pytest
import sqlite3 as sq
from contextlib import closing

from book_funcs import insert_book, insert_phys_book
from sql_funcs import init_db
from user_funcs import register


def test_users_books(tst_users, tst_books, test_db):
    init_db(test_db)
    for username, password, role in tst_users:
        result = register(username=username,
                          password=password,
                          role=role,
                          path=test_db)
        assert result is True


    for isbn, name, description, author, year, publication_year in tst_books:
        result = insert_book(isbn=isbn,
                             name=name,
                             description=description,
                             author=author,
                             year=year,
                             publication_year=publication_year,
                             path=test_db)
        assert result is True

    for book_id, book in enumerate(tst_books, 1):
        for _ in range(2):
            result = insert_phys_book(book_id=book_id, path=test_db)
            assert result is True

    with closing(sq.connect(test_db)) as conn:
        count_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        count_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        count_phys = conn.execute("SELECT COUNT(*) FROM book_copies").fetchone()[0]

    assert count_users == 5
    assert count_books == 4
    assert count_phys == 8

