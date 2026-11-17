import sqlite3 as sq
import os
from dotenv import load_dotenv

load_dotenv()

PATH = os.getenv("PATH_TO_DB")


def init_db() -> None:
    """

    :return: Initial database creation
    """

    with sq.connect(PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'reader'
                CHECK (role in ('reader', 'librarian')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT DEFAULT NULL
        )
        """)


def find_user(username: str, path: str) -> tuple | None:
    """
    :param username: string username of the user you want to find
    :param path: string path to the db file
    :return: tuple if user is found else if user is not found or exception was caught None
    """
    try:
        with sq.connect(path) as conn:
            result = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        return result
    except (sq.OperationalError, sq.InterfaceError, sq.DatabaseError) as e:
        print(f"[ERROR] {e}")
        return None


def insert_user(username: str, password: str) -> bool:
    """
    :param username: any valid username
    :param password: any valid password
    :return: True if user is inserted into the database else False
    """
    try:
        with sq.connect(PATH) as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password),
            )
        return True
    except sq.Error as e:
        print(f"[ERROR] {e}")
    return False


if __name__ == "__main__":
    print(PATH)
