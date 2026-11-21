from datetime import datetime
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
