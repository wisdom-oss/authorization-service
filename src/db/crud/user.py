from typing import List, Optional

from sqlalchemy.orm import Session
from ..objects import user


def get_user_by_id(db: Session, user_id: int) -> Optional[user.User]:
    """Get a ORM user object by the user id.

    :param db: Database Session which will be used to connect to the database
    :param user_id: ID of the user
    :return: If there is no user with the given id None will be returned
    """
    return db.query(user.User).filter(user.User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[user.User]:
    """Get a ORM user object by the username

    :param db: Database Session which will be used to connect to the database
    :param username: Username of the user
    :return: The user or if there is no user by this username None
    """
    return db.query(user.User).filter(user.User.username == username).first()


def get_users(db: Session) -> List[user.User]:
    """Get all users in the database

    :param db: Session which will be used to connect to the database
    :return: List of users
    """
    return db.query(user.User).all()
