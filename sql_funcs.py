import os
import sqlite3 as sq
from contextlib import closing
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PATH = BASE_DIR / "data" / "library.db"

ALLOWED_TABLES_INSERT = {
    "books": ("name", "description", "author", "year", "publication_year", "isbn"),
    "book_copies": ("book_id", "status"),
    "users": ("username", "password_hash", "role", "deleted_at"),
    "loans": (
        "book_copy_id",
        "reader_id",
        "issued_by",
        "loaned_at",
        "due_at",
        "returned_at",
        "returned_to",
    ),
}

ALLOWED_TABLES_SELECT = {
    "books": (
        "book_id",
        "name",
        "description",
        "author",
        "year",
        "publication_year",
        "added_at",
        "isbn",
    ),
    "book_copies": ("book_copy_id", "book_id", "added_at", "status"),
    "users": ("user_id", "username", "role", "created_at", "deleted_at"),
    "loans": (
        "loan_id",
        "book_copy_id",
        "reader_id",
        "issued_by",
        "loaned_at",
        "due_at",
        "returned_at",
        "returned_to",
    ),
}


def init_db(path: str = PATH) -> None:
    with closing(sq.connect(path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'reader'
                    CHECK(role IN ('reader', 'librarian')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT DEFAULT NULL,
                PRIMARY KEY(user_id AUTOINCREMENT)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                author TEXT,
                year INTEGER,
                publication_year INTEGER,
                added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                isbn TEXT NOT NULL
                    CHECK(LENGTH("isbn") = 13 AND "isbn" NOT GLOB '*[^0-9]*') UNIQUE,
                PRIMARY KEY(book_id AUTOINCREMENT)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS book_copies (
                book_copy_id INTEGER,
                book_id INTEGER NOT NULL,
                added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'available'
                    CHECK(status IN ('available', 'lost', 'retired')),
                PRIMARY KEY(book_copy_id AUTOINCREMENT),
                FOREIGN KEY(book_id) REFERENCES books(book_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER,
                book_copy_id INTEGER NOT NULL,
                reader_id INTEGER NOT NULL,
                issued_by INTEGER NOT NULL,
                loaned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                due_at TEXT NOT NULL,
                returned_at TEXT DEFAULT NULL,
                returned_to INTEGER DEFAULT NULL,
                PRIMARY KEY(loan_id AUTOINCREMENT),
                FOREIGN KEY(book_copy_id)
                    REFERENCES book_copies(book_copy_id),
                FOREIGN KEY(issued_by)
                    REFERENCES users(user_id),
                FOREIGN KEY(reader_id)
                    REFERENCES users(user_id)
            )
        """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS unique_active_loan 
            ON loans(book_copy_id) 
            WHERE returned_at IS NULL;
        """)


def validate_sql_columns(
    param_names: tuple, params: tuple, table: str, mode: str = "insert"
) -> tuple | None:
    if mode.lower() == "insert":
        white_list = ALLOWED_TABLES_INSERT
    elif mode.lower() == "select":
        white_list = ALLOWED_TABLES_SELECT
    else:
        return None

    if len(param_names) != len(params):
        return None

    if not params or not param_names:
        return None

    try:
        table = table.lower()
        param_names = tuple(map(str.lower, param_names))
    except (ValueError, TypeError, AttributeError) as e:
        print(f"[ERROR] {e}")
        return None

    if len(param_names) != len(set(param_names)):
        return None

    allowed_columns = white_list.get(table)

    if allowed_columns is None:
        return None

    if not set(param_names).issubset(allowed_columns):
        return None

    return table, param_names


def insert_any_sql(
    param_names: tuple, params: tuple, table: str, path: str = PATH
) -> int | None:
    if not (temp := validate_sql_columns(param_names, params, table, "insert")):
        return None

    table = temp[0]
    param_names = temp[1]

    try:
        with closing(sq.connect(path, timeout=10)) as conn:
            with conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                inserted_id = conn.execute(
                    f"INSERT INTO {table} ({', '.join(param_names)}) VALUES ({'?, ' * (len(params) - 1)}?)",
                    params,
                ).lastrowid
        return inserted_id
    except sq.Error as e:
        print(f"[ERROR] {e}")
    return None


def select_records(
    param_names: tuple, params: tuple, table: str, fetch: str = "one", path: str = PATH
) -> sq.Row | tuple[sq.Row] | None:
    if not (temp := validate_sql_columns(param_names, params, table, "select")):
        return None

    table = temp[0]
    param_names = temp[1]

    if fetch not in ("one", "all"):
        return None

    try:
        with closing(sq.connect(path, timeout=5)) as conn:
            sql = f"SELECT * FROM {table} WHERE {' = ? AND '.join(param_names)} = ?"
            parameters = params
            with conn:
                conn.row_factory = sq.Row
                conn.execute("PRAGMA foreign_keys = ON;")
                if fetch == "one":
                    result = conn.execute(sql, parameters).fetchone()
                else:
                    result = tuple(conn.execute(sql, parameters).fetchall())
        return result if result else None
    except (sq.OperationalError, sq.InterfaceError, sq.DatabaseError) as e:
        print(f"[ERROR] {e}")
        return None


if __name__ == "__main__":
    init_db()
