"""Package for the CREATE/READ/UPDATE/DELETE utilities"""
import typing

from sqlalchemy.orm import Session
from passlib.hash import pbkdf2_sha512 as pass_hash

import models.http.outgoing
import models.shared
from models.http.incoming import NewUserAccount

from .. import tables

DBObject = typing.TypeVar(
    'DBObject',
    tables.Account, tables.Scope, tables.Role,
    tables.AccessToken, tables.RefreshToken, tables.AccountToRoles,
    tables.AccountToScope, tables.AccountToToken,
    tables.AccountToRefreshTokens, tables.RoleToScope,
    tables.TokenToScopes, tables.TokenToRefreshToken
)
"""Generic type for all database inserts"""


def add_to_database(obj: DBObject, session: Session) -> DBObject:
    """Insert a new object into the database

    :param obj: Object which shall be inserted
    :type obj: X
    :param session: Database session
    :return: The inserted object
    """
    # Insert the object into the database
    session.add(obj)
    # Commit the changes made to the database
    session.commit()
    # Refresh the object
    session.refresh(obj)
    # Return the refreshed object
    return obj


def get_all(table: typing.Type[DBObject], session: Session) -> list[DBObject]:
    """Get all present entries of a table

    :param table: The table which shall be returned
    :param session: The session used to get the table entries
    :return: A list of entries
    """
    return session.query(table).all()


# ==== Account-Table operations ====
def get_user(user_id: int, session: Session) -> typing.Optional[tables.Account]:
    """Get an account by its internal id

    :param user_id: The internal user id
    :param session: Database connection
    :return: The account data from the database
    """
    return (session
            .query(tables.Account)
            .filter(tables.Account.account_id == user_id)
            .first()
            )


def get_user_by_username(username: str, session: Session) -> typing.Optional[tables.Account]:
    """Get a users account by a username

    :param username: The username of the account
    :param session: Database session
    :return: None if the user does not exist, else the orm account
    """
    return (session
            .query(tables.Account)
            .filter(tables.Account.username == username)
            .first()
            )


def add_user(new_user: NewUserAccount, session: Session) -> tables.Account:
    """Add a new user to the database

    :param new_user: New user which shall be created
    :param session: Database connection
    :return: The created user
    """
    # Translate the data model into an orm model
    account: tables.Account = tables.Account(
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        username=new_user.username,
        is_active=True
    )
    # Hash the password and add it to the orm model
    account.password = pass_hash.hash(new_user.password.get_secret_value())
    # Insert the db object
    account = add_to_database(account, session)
    # Split the scope string and assign the scopes to the user
    for scope in new_user.scopes.split():
        map_scope_to_account(scope, account.account_id, session)
    # Iterate through the role names
    for role in new_user.roles:
        map_role_to_account(role, account.account_id, session)
    # Refresh the user one last time
    session.refresh(account)
    # Return the account
    return account


# ==== Scope-Table operations ====
def get_scope(scope_id: int, session: Session) -> typing.Optional[tables.Scope]:
    """Get a scope from the database by its internal id

    :param scope_id: Internal ID of the scope
    :param session: Database session
    :return: None if the scope does not exist, else the scope orm
    """
    return session.query(tables.Scope).filter(tables.Scope.scope_id == scope_id).first()


def get_scope_by_value(scope_value: str, session: Session) -> typing.Optional[tables.Scope]:
    """Get a scope from the database by its scope value

    :param scope_value: Value of the scope for the scope string
    :param session: Database session
    :return: None if the scope does not exist, else the orm representation of the scope
    """
    return session.query(tables.Scope).filter(tables.Scope.scope_value == scope_value).first()


def add_scope(new_scope: models.shared.Scope, session: Session) -> tables.Scope:
    """Add a new Scope to the system

    :param new_scope: The new scope for the environment
    :param session: The database session used to insert it
    :return: The inserted scope
    """
    scope = tables.Scope(
        **new_scope.dict()
    )
    return add_to_database(scope, session)


# ==== Access-Token table operations ====
def get_access_token(token_id: int, session: Session) -> typing.Optional[tables.AccessToken]:
    """Get an access token from the database by its internal id

    :param token_id: Internal Access Token ID
    :param session: Database session
    :return: If the token exists the token, else None
    """
    return session.query(tables.AccessToken).filter(tables.AccessToken.token_id == token_id).first()


def get_access_token_by_token(
        token_value: str,
        session: Session
) -> typing.Optional[tables.AccessToken]:
    """Get an access token from the database by its actual value

    :param token_value: The actual value of the access token
    :param session: Database session
    :return: If the token exists the token, else None
    """
    return session.query(tables.AccessToken).filter(tables.AccessToken.token == token_value).first()


def delete_access_token(token_id: int, session: Session):
    """Delete an access token from the database

    :param token_id:
    :param session:
    :return:
    """
    session.query(tables.AccessToken).filter(tables.AccessToken.token_id == token_id).delete()


# ==== Refresh-Token table operations ====
def get_refresh_token(token_id: int, session: Session) -> typing.Optional[tables.RefreshToken]:
    """Get an access token from the database by its internal id

    :param token_id: Internal Access Token ID
    :param session: Database session
    :return: If the token exists the token, else None
    """
    return (session
            .query(tables.RefreshToken)
            .filter(tables.RefreshToken.refresh_token_id == token_id)
            .first()
            )


def get_refresh_token_by_token(
        token_value: str,
        session: Session
) -> typing.Optional[tables.RefreshToken]:
    """Get an access token from the database by its actual value

    :param token_value: The actual value of the access token
    :param session: Database session
    :return: If the token exists the token, else None
    """
    return (session
            .query(tables.RefreshToken)
            .filter(tables.RefreshToken.refresh_token == token_value)
            .first()
            )


def delete_refresh_token(token_id: int, session: Session):
    """Delete an access token from the database

    :param token_id:
    :param session:
    :return:
    """
    (session
     .query(tables.RefreshToken)
     .filter(tables.RefreshToken.refresh_token_id == token_id).delete())


# ==== Role-Table operations ====
def get_role(role_id: int, session: Session) -> tables.Role:
    """Get a role by its id

    :param role_id: The internal role id
    :param session: The database session used to retrieve the role
    :return: The role if it was found, else None
    """
    return session.query(tables.Role).filter(tables.Role.role_id == role_id).first()


def add_role(new_role: models.http.incoming.Role, session: Session) -> tables.Role:
    """Add a new role to the system

    :param new_role: The role which shall be inserted
    :param session: The session used to insert the role
    :return: The inserted role
    """
    role = tables.Role(
        role_name=new_role.role_name,
        role_description=new_role.role_description
    )
    role = add_to_database(role, session)
    if new_role.role_scopes is not None and new_role.role_scopes.strip() != "":
        for scope in new_role.role_scopes.split():
            map_scope_to_role(role.role_id, scope, session)
    return role


# ==== Mapping-Table operations ====
def map_scope_to_account(
        scope_value: str,
        account_id: int,
        session: Session
) -> typing.Optional[tables.AccountToScope]:
    """Map a scope to the account

    :param scope_value: Value of the scope to be assigned
    :param account_id: Internal id of the account which shall be using this scope,
    :param session: Database session
    :return: The assignment if the scope exists and was assigned, else None
    """
    # Get the scope object to retrieve its internal id
    scope: tables.Scope = (session.query(tables.Scope)
                           .filter(tables.Scope.scope_value == scope_value)
                           .first())
    # Check if a scope with this value exists
    if scope is not None:
        # If a scope exists: create a new assignment entry
        _assignment_entry: tables.AccountToScope = tables.AccountToScope(
            account_id=account_id,
            scope_id=scope.scope_id
        )
        return add_to_database(_assignment_entry, session)
    # Return None to show that no scope with this name exists
    return None


def map_role_to_account(role_name: str, account_id: int, session: Session):
    """Map a role to an account

    :param role_name: Name of the role
    :param account_id: Internal account id
    :param session: Database connection
    :return: The association object if the insert was successful, else None
    """
    # Get the role object for retrieving the internal role id
    role: tables.Role = (
            session
            .query(tables.Role)
            .filter(tables.Role.role_name == role_name)
            .first()
    )
    # Check if the role exists
    if role is not None:
        _assignment_entry: tables.AccountToRoles = tables.AccountToRoles(
            account_id=account_id,
            role_id=role.role_id
        )
        return add_to_database(_assignment_entry, session)
    # No role with that name exists
    return None


def map_scope_to_role(role_id: int, scope_value: str, session: Session):
    """Map a scope to a role

    :param session: Database session
    :param role_id: Internal ID of the role
    :param scope_value: Name of the scope which shall be mapped to the role
    """
    # Get the scope
    _scope = get_scope_by_value(scope_value, session)
    if _scope is not None:
        _mapping = tables.RoleToScope(
            role_id=role_id,
            scope_id=_scope.scope_id
        )
        return add_to_database(_mapping, session)
    return None


def clear_mapping_entries(
        table: typing.Type[tables.RoleToScope],
        main_key: int,
        db_session: Session
):
    """Clear all mapping entries with the role id

    :param table: The mapping table which shall be cleared for the
    :param main_key:
    :param db_session:
    :return:
    """
    db_session.query(table).filter(table.role_id == main_key).delete()


def get_client_credential_by_client_id(client_id: str, session: Session) -> tables.ClientCredential:
    """Get a client credential from the database

    :param client_id: The client id which shall be queried for
    :param session: The database session used to access the database
    :return:
    """
    return (session
            .query(tables.ClientCredential)
            .filter(tables.ClientCredential.client_id == client_id)
            .first())


def get_client_credential(credential_id, session):
    return (session
            .query(tables.ClientCredential)
            .filter(tables.ClientCredential.credential_id == credential_id)
            .first())
