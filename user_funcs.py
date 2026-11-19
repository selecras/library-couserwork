from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError, VerificationError
from sql_funcs import select_records, PATH, insert_any_sql

ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def hash_password(password: str) -> str | None:
    try:
        return ph.hash(password)
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def verify_password(hashed: str, password: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except (InvalidHashError, VerificationError) as e:
        print(f"[ERROR] {e}")
        return False


def validate_password(password: str) -> bool:
    upper_alp = "QWERTYUIOPASDFGHJKLZCVBNM"
    lower_alp = "qwertyuiopasdfghjklzxcvbnm"
    nums = "0123456789"
    special = "_-.!@#$%^&*()+=[];:,<>"
    check_low = False
    check_up = False
    check_num = False
    check_spec = False

    if not password:
        return False

    if not (8 <= len(password) <= 64):
        return False

    if any(i for i in password if i not in upper_alp + lower_alp + nums + special):
        return False

    for letter in password:
        if letter in upper_alp:
            check_up = True
        if letter in lower_alp:
            check_low = True
        if letter in nums:
            check_num = True
        if letter in special:
            check_spec = True
        if all((check_up, check_low, check_num, check_spec)):
            return True
    return False


def validate_username(username: str) -> bool:
    alp = "qwertyuiopasdfghjklzxcvbnm1234567890_-."
    not_first = "_-."

    if not username:
        return False

    if not (3 <= len(username) <= 16):
        return False

    if username[0] in not_first:
        return False

    for letter in username:
        if letter.lower() not in alp:
            return False

    return True


def register(username: str, password: str, path: str = PATH) -> bool:
    username = username.strip().lower()
    if not (validate_password(password)) or not (validate_username(username)):
        return False
    try:
        password = hash_password(password)
        if not password:
            print("[ERROR] Unable to hash password")
            return False
        return insert_any_sql(
            ("username", "password_hash"), (username, password), "users", path
        )
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def login(username: str, password: str) -> bool:
    username = username.strip().lower()
    user = select_records(param_names=("username",), params=(username,), table="users")
    return not (
        user is None or user[5] is not None or not (verify_password(user[2], password))
    )
