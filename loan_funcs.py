import sqlite3 as sq
from datetime import datetime, timezone
from sql_funcs import select_records, PATH, validate_date


def find_available_copy(book_id: int) -> int | None:
    book = select_records(("book_id",), (book_id,), 'books', 'one')
    book_copies = select_records(('book_id',), (book_id,), 'book_copies', 'all')

    if not book or not book_copies:
        return None
    for book_copy in book_copies:
        if book_copy[3] == 'available':
            return book_copy[0]
    return None


def issue_book(book_id: int, reader_id: int, issued_by: int, due_at: str, path: str=PATH):
    book = select_records(("book_id",), (book_id,), 'books', 'one')
    reader = select_records(("user_id",), (reader_id,), "users", 'one')
    librarian = select_records(("user_id",), (issued_by,), "users", 'one')
    book_copies = select_records(('book_id',), (book_id,), 'book_copies', 'all')
    book_copy_id = find_available_copy(book_id)

    if not book or not reader or not book_copies or not librarian or not book_copy_id:
        return False

    if not (due_at := validate_date(due_at)):
        return False

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if due_at < now:
        return False

    try:
        with sq.connect(path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute(
                "UPDATE book_copies SET status = loaned WHERE book_copy_id = ?",
                (book_copy_id,)
            )
            conn.execute(
                "INSERT INTO loans (book_copy_id, reader_id, issued_by, due_at) VALUES (?, ?, ?, ?)",
                (book_copy_id, reader_id, issued_by, due_at)
            )
        return True
    except sq.Error as e:
        print(f"[ERROR] {e}")
        return False


def return_book():
    pass


if __name__ == "__main__":
    pass
    # utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    # print(utc_now)
    # print(datetime.strptime(utc_now, "%Y-%m-%d %H:%M:%S"))