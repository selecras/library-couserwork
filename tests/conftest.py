import pytest


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "library_test.db"
    return str(db_path)


@pytest.fixture
def tst_users():
    users = [("sorphq", "AbCdefg123!@#", "librarian"),
             ("timur123", "FHSgafGDSA38*@41(", "librarian"),
             ("qunife", "qWWe123!@#!@#!", "reader"),
             ("zuthely", "kgd!@#ashgLASHhgk12!@3(#", "reader"),
             ("hacker", "Im_Not_A_Hacker_123!@#($@", "reader")]
    return users

@pytest.fixture
def tst_books():
    books = [("2862052806270", "Пособие по уязвимостям", "", "Карина Гарипова", 2020, 2021),
             ("3304781537104", "Ро!!", "Коротенькие Гениалища", "Л.И.Ф.", 1986, 1986),
             ("3663787090243", "1984", "Популярный роман-антиутопия о тоталитарном обществе", "Джордж Оруэлл", 1948, 2025),
             ("7546450034354", "Искусство войны", "Древнекитайский трактат по военной стратегии и политике", "Сунь-цзы", -495, 2000)]
    return books


@pytest.fixture
def tst_single_user():
    users = ("sorphq", "AbCdefg123!@#")
    return users