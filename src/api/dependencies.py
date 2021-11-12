"""Module for extra dependencies like own request bodies or database connections"""
from db import DatabaseSession


def get_db_session() -> DatabaseSession:
    """Get a opened Database session which can be used to manipulate orm data

    :return: Database Session
    :rtype: DatabaseSession
    """
    db = DatabaseSession()
    try:
        yield db
    finally:
        db.close()
