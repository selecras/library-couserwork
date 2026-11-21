import sqlite3 as sq
from datetime import datetime, timezone
from sql_funcs import PATH


def validate_date(date: str) -> datetime | None:
    try:
        check = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        return check
    except ValueError:
        print("[ERROR] Invalid date")
        return None


def issue_book(
    book_id: int, reader_id: int, issued_by: int, due_at: str, path: str = PATH
) -> bool:
    connection_created = False
    if not (due_at := validate_date(due_at)):
        return False

    now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
    if due_at < now:
        return False

    due_at = str(due_at)

    try:
        with sq.connect(path, timeout=10, autocommit=True) as conn:
            connection_created = True
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
                or reader[3] != "reader"
                or reader[5] is not None
                or librarian[3] != "librarian"
                or librarian[5] is not None
            ):
                conn.execute("ROLLBACK")
                return False

            book_copy_id = book_copy_id[0]

            conn.execute(
                "INSERT INTO loans (book_copy_id, reader_id, issued_by, due_at) VALUES (?, ?, ?, ?)",
                (book_copy_id, reader_id, issued_by, due_at),
            )
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


def return_book(loan_id: int, returned_to: int, path: str=PATH) -> bool:
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
                AND deleted_at IS NULL""").fetchone()

            if not librarian:
                conn.execute("ROLLBACK")
                return False

            is_updated = conn.execute("""
            UPDATE loans
            SET returned_at = CURRENT_TIMESTAMP,
                returned_to = ?
            WHERE loan_id = ?
                AND returned_at IS NULL""",
            (returned_to, loan_id)
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
