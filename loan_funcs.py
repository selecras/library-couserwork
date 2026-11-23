import sqlite3 as sq
from contextlib import closing
from datetime import datetime, timezone
from sql_funcs import PATH


def validate_date(date: str) -> datetime | None:
    try:
        check = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        return check
    except (ValueError, TypeError):
        print("[ERROR] Invalid date")
        return None


def issue_book(
    book_id: int, reader_id: int, issued_by: int, due_at: str, path: str = PATH
) -> int | None:
    """
    :param book_id: id of the book (not copy)
    :param reader_id: id of the reader
    :param issued_by: id of the librarian
    :param due_at: YYYY-MM-DD HH:MM:SS
    :param path: path to the database
    :return:
    """
    connection_created = False
    if not (due_at := validate_date(due_at)):
        return None

    now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
    if due_at < now:
        return None

    due_at = str(due_at)

    try:
        with sq.connect(path, timeout=10, autocommit=True) as conn:
            connection_created = True
            conn.row_factory = sq.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("BEGIN IMMEDIATE")

            reader = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (reader_id,)
            ).fetchone()
            librarian = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (issued_by,)
            ).fetchone()
            book_copy_id = conn.execute(
                """
                        SELECT *
                        FROM book_copies as bc
                        WHERE bc.book_id = ?
                            AND bc.status = 'available'
                            AND NOT EXISTS (
                                SELECT 1
                                FROM loans as l
                                WHERE l.book_copy_id = bc.book_copy_id
                                    AND l.returned_at IS NULL
                        )
                        ORDER BY bc.book_copy_id
                        LIMIT 1""",
                (book_id,),
            ).fetchone()

            if (
                not reader
                or not librarian
                or not book_copy_id
                or reader["role"] != "reader"
                or reader["deleted_at"] is not None
                or librarian["role"] != "librarian"
                or librarian["deleted_at"] is not None
            ):
                conn.execute("ROLLBACK")
                return None

            book_copy_id = book_copy_id[0]

            loan_id = conn.execute(
                "INSERT INTO loans (book_copy_id, reader_id, issued_by, due_at) VALUES (?, ?, ?, ?)",
                (book_copy_id, reader_id, issued_by, due_at),
            ).lastrowid
            conn.execute("COMMIT")
        return loan_id
    except Exception as e:
        if connection_created:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
        print(f"[ERROR] {e}")
        return None
    finally:
        if connection_created:
            conn.close()


def return_book(loan_id: int, returned_to: int, path: str = PATH) -> bool:
    connection_created = False

    try:
        with sq.connect(path, timeout=10, autocommit=True) as conn:
            connection_created = True
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("BEGIN IMMEDIATE")

            librarian = conn.execute("""
            SELECT 1 FROM users 
            WHERE user_id = ? 
                AND role = 'librarian'
                AND deleted_at IS NULL""", (returned_to,)).fetchone()

            if not librarian:
                conn.execute("ROLLBACK")
                return False

            is_updated = conn.execute(
                """
            UPDATE loans
            SET returned_at = CURRENT_TIMESTAMP,
                returned_to = ?
            WHERE loan_id = ?
                AND returned_at IS NULL""",
                (returned_to, loan_id),
            ).rowcount

            if is_updated != 1:
                conn.execute("ROLLBACK")
                return False

            conn.execute("COMMIT")
        return True
    except Exception as e:
        if connection_created:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
        print(f"[ERROR] {e}")
        return False
    finally:
        if connection_created:
            conn.close()


def get_user_loans(user_id, path: str = PATH) -> dict | None:
    try:
        with closing(sq.connect(path)) as conn:
            conn.row_factory = sq.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            data = conn.execute("""
            SELECT loan_id, name, author, loaned_at, due_at, returned_at
            FROM loans AS l
            JOIN book_copies AS bc
                ON l.book_copy_id = bc.book_copy_id
            JOIN books AS b
                ON bc.book_id = b.book_id
            WHERE l.reader_id = ?
            ORDER BY l.due_at
            """, (user_id,)
            ).fetchall()
    except sq.Error as e:
        print(f"[ERROR] {e}")
        return None

    loaned = [dict(i) for i in data if i["returned_at"] is None]
    returned = [dict(i) for i in data if i["returned_at"] is not None]

    return {
        "loaned": loaned,
        "returned": returned
            }


if __name__ == "__main__":
    pass
    # return_book(5, 1)
    # issue_book(1, 2, 1, "2026-11-23 07:25:07")
    # issue_book(2, 2, 1, "2026-11-29 06:44:07")
    # issue_book(3, 2, 1, "2026-11-29 06:44:07")
    # issue_book(4, 2, 1, "2026-11-29 06:44:07")