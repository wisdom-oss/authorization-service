"""Package for the CREATE/READ/UPDATE/DELETE utilities"""

# ==== Account-Table operations ====
import logging
from typing import Optional

from passlib.hash import pbkdf2_sha512 as pass_hash
from sqlalchemy.orm import Session

from database import Account
from database import tables
from models.incoming import NewUserAccount
from models.outgoing import UserAccount


def add_new_user(account: NewUserAccount, session: Session) -> UserAccount:
    """Create a new user in the database

    :param account: The account which shall be created
    :type account: NewUserAccount
    :param session: Database connection
    :type session: Session
    :return: The created account
    :rtype: UserAccount
    """
    # Create a new database object account without any password
    __db_account: Account = Account(
        first_name=account.first_name,
        last_name=account.last_name,
        username=account.username,
        is_active=True
    )
    # Hash the password for the new account
    __db_account.password = pass_hash.hash(account.password.get_secret_value())
    # Add the account to the database
    session.add(__db_account)
    # Commit the changes made to the database
    session.commit()
    # Refresh the database object to retrieve the internal id
    session.refresh(__db_account)
    # Split the scope string and assign the scopes to the account
    for scope in account.scopes.split(' '):
        if map_scope_to_account(scope, __db_account.account_id, session) is None:
            logging.getLogger("DB.CRUD").warning('The scope "{}" does not exist. Therefore it was '
                                                 'not inserted', scope)
    for role in account.roles:
        # TODO: Implement CRUD for assigning role to account (by internal account id)
        pass
    # Commit all changes to the database
    session.commit()
    # Refresh the user account
    session.refresh(__db_account)
    # Create a user account object
    return UserAccount.parse_obj(__db_account)


# ==== Mapping-Table operations ====
def map_scope_to_account(
        scope_value: str,
        account_id: int,
        session: Session
) -> Optional[tables.AccountToScope]:
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
        # Add the assignment entry to the database
        session.add(_assignment_entry)
        # Commit the changes and refresh the assignment
        session.commit()
        session.refresh(_assignment_entry)
        return _assignment_entry
    else:
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
    role: tables.Role = (session.query(tables.Role)
                         .filter(tables.Role.role_name == role_name)
                         .first())
    # Check if the role exists
    if role is not None:
        # TODO: Implement insert
        pass
    else:
        return None

