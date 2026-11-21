import pytest

from sql_funcs import init_db, select_records
from user_funcs import register, login, delete_user


def test_users_registration(test_db):
    init_db(test_db)
    result = register("Sharipov_Timur", "qwe123!@#QWERTY", path=test_db)
    assert result is True
    user = select_records(("username",), ("sharipov_timur",), table='users', path=test_db)
    assert len(user) == 1


def test_double_registration(test_db):
    init_db(test_db)
    result_first = register("Sharipov_Timur", "qwe123!@#QWERTY", path=test_db)
    result_second = register(" sharipov_timur  ", "abdsaOUFw92!)$", path=test_db)
    assert result_first is True
    assert result_second is False

    users = select_records(("username",), ("sharipov_timur",), fetch='all', table='users', path=test_db)
    assert len(users) == 1


def test_invalid_registration(test_db):
    init_db(test_db)
    result_first = register("timur!@#", "qwe123!@#QWERTY", path=test_db)
    result_second = register("sorphq123", "qwerty123", path=test_db)
    result_third = register("is@#!", "12345678901234567890", path=test_db)
    assert result_first is False
    assert result_second is False
    assert result_third is False

    users = select_records(("username",), ("sharipov_timur",), fetch='all', table='users', path=test_db)
    assert len(users) == 0


def test_login(test_db):
    init_db(test_db)
    register("Sharipov_Timur", "qwe123!@#QWERTY", path=test_db)
    result_correct = login(" sharipov_timur  ", "qwe123!@#QWERTY", path=test_db)
    result_incorrect = login(" sharipov_timur  ", "qwe123123213!", path=test_db)
    assert result_correct is True
    assert result_incorrect is False


def test_soft_delete(test_db):
    init_db(test_db)
    register("Sharipov_Timur", "qwe123!@#QWERTY", path=test_db)
    result = delete_user(1, test_db) # user_id = 1 т.к. наша учётка -- это единственная запись во временной бд
    assert result is True

    user = select_records(("username",), ("sharipov_timur",), table='users', path=test_db)
    assert user[5] is not None # Проверяем, что ячейка deleted_at заполнена, т.е. аккаунт удалён

