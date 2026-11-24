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
) -> int | None:

    if year is not None:
        if not (-5000 <= year <= datetime.now().year):
            return None

    if publication_year is not None:
        if not (-5000 <= publication_year <= datetime.now().year):
            return None

    if year is not None and publication_year is not None:
        if publication_year < year:
            return None

    isbn = isbn.strip()
    if not validate_isbn(isbn):
        return None

    return insert_any_sql(
        ("name", "description", "author", "year", "publication_year", "isbn"),
        (name, description, author, year, publication_year, isbn),
        "books",
        path,
    )


def insert_phys_book(book_id: int, path: str = PATH) -> int | None:
    return insert_any_sql(("book_id",), (book_id,), "book_copies", path)


def get_books(
    path: str = PATH, to_get: tuple | list = ("name", "author", "year")
) -> list[dict] | None:
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

    data = [dict(i) for i in data]
    return data


def get_catalog_books(path: str=PATH) -> list[sq.Row] | None:
    try:
        with closing(sq.connect(path)) as conn:
            conn.row_factory = sq.Row
            data = conn.execute("""
            SELECT
                b.book_id,
                b.name,
                b.author,
                b.year,
                COUNT(bc.book_copy_id) as available_copies
            FROM books AS b
            LEFT JOIN book_copies AS bc
                ON b.book_id = bc.book_id
                AND bc.status = 'available'
                AND NOT EXISTS(
                    SELECT 1
                    FROM loans AS l
                    WHERE l.book_copy_id = bc.book_copy_id
                        AND l.returned_at IS NULL
            )
            GROUP BY b.book_id, b.name, b.author, b.year
            """).fetchall()
            return data
    except sq.Error as e:
        print(f"[ERROR] {e}")
        return None

if __name__ == "__main__":
    pass
