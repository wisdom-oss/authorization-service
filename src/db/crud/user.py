import random
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from .role import assign_user_to_role
from passlib.hash import pbkdf2_sha512
from db.crud.scope import assign_user_to_scope

import data_models
from db import objects


def get_user_by_id(db: Session, user_id: int) -> Optional[objects.User]:
    """Get a ORM user object by the user id.

    :param db: Database Session which will be used to connect to the database
    :param user_id: ID of the user
    :return: If there is no user with the given id None will be returned
    """
    return db.query(objects.User).filter(objects.User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[objects.User]:
    """Get a ORM user object by the username

    :param db: Database Session which will be used to connect to the database
    :param username: Username of the user
    :return: The user or if there is no user by this username None
    """
    return db.query(objects.User).filter(objects.User.username == username).first()


def get_users(db: Session) -> List[objects.User]:
    """Get all users in the database

    :param db: Session which will be used to connect to the database
    :return: List of users
    """
    return db.query(objects.User).all()


def add_user(db: Session, new_user: data_models.User) -> objects.User:
    """Add a new user to the database

    :param new_user: The user which shall be inserted
    :param db: Database session
    :return: Database ORM user
    """
    _password_hash = pbkdf2_sha512.hash(new_user.password, salt_size=random.randint(32, 1024))
    db_user = objects.User(
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        username=new_user.username,
        password=_password_hash,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    for scope in new_user.scopes:
        assign_user_to_scope(db, scope.id, db_user.user_id)
    for role in new_user.roles:
        assign_user_to_role(db, db_user.user_id, role.id)
    # Refresh the user after assigning the scopes and roles
    db.refresh(db_user)
    return db_user


def remove_user(db: Session, user_id: int):
    """Remove a user from the database. The user may only be removed if the user_id is known

    :param db: Database Session
    :param user_id: ID of the User which shall be removed
    :return:
    """
    db_user = db.query(objects.User).filter(objects.User.user_id == user_id).first()
    db.delete(db_user)
    db.commit()


def update_user(db: Session, user_id: int, **new_values) -> objects.User:
    """Update a user account

    :param db: Database session
    :param user_id: ID of the user which will be updated
    :param new_values: New values for the account. Available arguments are: first_name, last_name,
        username, password, scopes, roles.
        When passing scopes or roles all scopes or roles need to be passed to the function.
    :return: The updated user
    """
    if 'first_name' in new_values:
        db.execute(
            update(objects.User)
            .where(objects.User.user_id == user_id)
            .values(first_name=new_values.get('first_name'))
        )
    if 'last_name' in new_values:
        db.execute(
            update(objects.User)
            .where(objects.User.user_id == user_id)
            .values(last_name=new_values.get('last_name'))
        )
    if 'username' in new_values:
        db.execute(
            update(objects.User)
            .where(objects.User.user_id == user_id)
            .values(username=new_values.get('username'))
        )
    if 'password' in new_values:
        _password_hash = pbkdf2_sha512.hash(
            new_values.get('password'),
            salt_size=random.randint(32, 1024)
        )
        db.execute(
            update(objects.User)
            .where(objects.User.user_id == user_id)
            .values(password=_password_hash)
        )
    if 'scopes' in new_values:
        db.query(delete(objects.UserScope).where(objects.UserScope.user_id == user_id))
        for scope in new_values.get('scopes'):
            assign_user_to_scope(db, user_id, scope.id)
    if 'roles' in new_values:
        db.query(delete(objects.UserRole).where(objects.UserRole.user_id == user_id))
        for role in new_values.get('roles'):
            assign_user_to_role(db, user_id, role.id)
    # Return the updated user
    return db.query(objects.User).filter(objects.User.user_id == user_id).first()
