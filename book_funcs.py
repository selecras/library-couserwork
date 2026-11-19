from datetime import datetime
from sql_funcs import insert_any_sql, PATH


def insert_book(
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

    return insert_any_sql(
        ("name", "description", "author", "year", "publication_year"),
        (name, description, author, year, publication_year),
        "books",
        path,
    )


def insert_phys_book(book_id: int, path: str = PATH) -> bool:
    return insert_any_sql(("book_id",), (book_id,), "book_copies", path)
