from app.database.mongodb import check_connection


def test_mongodb_connection():
    assert check_connection() is True
