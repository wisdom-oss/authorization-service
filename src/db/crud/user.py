import random
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from api.exceptions import ObjectNotFoundException
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


def add_user(db: Session, new_user: data_models.NewUser) -> objects.User:
    """Add a new user to the database

    :param new_user: The user which shall be inserted
    :param db: Database session
    :return: Database ORM user
    """
    _password_hash = pbkdf2_sha512.hash(
        new_user.password.get_secret_value(),
        salt_size=random.randint(32, 1024)
    )
    db_user = objects.User(
        first_name=new_user.first_name.strip(),
        last_name=new_user.last_name.strip(),
        username=new_user.username.strip(),
        password=_password_hash,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    for scope in new_user.scopes.split(" "):
        assign_user_to_scope(db, db_user.user_id, scope)
    for role in new_user.roles:
        assign_user_to_role(db, db_user.user_id, role)
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
    if db_user is not None:
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
    _user = get_user_by_id(db, user_id)
    if _user is None:
        raise ObjectNotFoundException()
    print(_user.username)
    print(new_values)
    if 'first_name' in new_values and new_values['first_name'].strip() != "":
        _user.first_name = new_values['first_name'].strip()
    if 'last_name' in new_values and new_values['last_name'].strip() != "":
        _user.last_name = new_values['last_name'].strip()
    if 'username' in new_values and new_values['username'].strip() != "":
        _user.username = new_values['username'].strip()
    if 'password' in new_values and new_values['password'].strip() != "":
        _password_hash = pbkdf2_sha512.hash(
            new_values['password'],
            salt_size=random.randint(32, 1024)
        )
        _user.password = _password_hash
    if 'scopes' in new_values and new_values["scopes"] is not None:
        db.query(objects.UserScope).filter(objects.UserScope.user_id == user_id).delete()
        db.commit()
        for scope in new_values.get('scopes').split(" "):
            assign_user_to_scope(db, user_id, scope)
            db.commit()
    if 'roles' in new_values and new_values["roles"] is not None:
        db.query(objects.UserRole).filter(objects.UserRole.user_id == user_id).delete()
        db.commit()
        for role in new_values.get('roles'):
            assign_user_to_role(db, user_id, role.id)
    # Commit the changes made to the database
    db.commit()
    # Return the updated user
    return db.query(objects.User).filter(objects.User.user_id == user_id).first()
