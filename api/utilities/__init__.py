"""This package holds some utilities which are used multiple times in the api implementation"""
import time
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

import database.tables
import models.outgoing

ACCESS_TOKEN_TTL = 3600
"""TTL for a access token in seconds (1h)"""

REFRESH_TOKEN_TTL = 604800
"""TTL for a refresh token in seconds (7d)"""


def generate_token_set(
        user: database.tables.Account,
        db_session: Session,
        scopes: Optional[List[str]] = None
) -> models.outgoing.TokenSet:
    """Generate a new token set and insert it into the database

    :param db_session: The Database connection used to insert the token set
    :param user: The user for which the token set shall be generated
    :param scopes: The scopes this token is valid for (optional, defaults to any scope the user
    has assigned)
    :return: The generated Token Set
    """
    # Save the generation time
    _generation_time: int = int(time.time())
    # Generate a database token object
    _token = database.tables.AccessToken(
        token=str(uuid.uuid4()),
        expires=_generation_time + ACCESS_TOKEN_TTL,
        created=_generation_time,
        active=True
    )
    # Insert the created Access Token into the database
    _token = database.crud.add_to_database(_token, db_session)
    # Assign the created access token to a user
    _token_assignment = database.tables.AccountToToken(
        account_id=user.account_id,
        token_id=_token.token_id
    )
    # Insert the created mapping into the database
    _token_assignment = database.crud.add_to_database(_token_assignment, db_session)
    # Map the scopes to the token
    if scopes is None:
        # Use the scopes the user owns
        for scope in user.scopes:
            # Create a mapping entry
            _token_scope_mapping = database.tables.TokenToScopes(
                token_id=_token.token_id,
                scope_id=scope.scope_id
            )
            # Insert the mapping into the database
            database.crud.add_to_database(_token_scope_mapping, db_session)
    else:
        for scope_value in scopes:
            # Get the scope data from the database
            _scope = database.crud.get_scope_by_value(scope_value, db_session)
            # Check if the scope still exists
            if _scope is not None:
                # Create a mapping entry
                _token_scope_mapping = database.tables.TokenToScopes(
                    token_id=_token.token_id,
                    scope_id=_scope.scope_id
                )
                # Insert the mapping into the database
                database.crud.add_to_database(_token_scope_mapping, db_session)

    # Create a refresh token for the account
    _refresh_token = database.tables.RefreshToken(
        refresh_token=str(uuid.uuid4()),
        expires=_generation_time + REFRESH_TOKEN_TTL
    )
    # Add the refresh token to the database
    _refresh_token = database.crud.add_to_database(_refresh_token, db_session)
    # Generate a mapping between the refresh token and the user account
    _refresh_token_assignment = database.tables.AccountToRefreshTokens(
        account_id=user.account_id,
        refresh_token_id=_refresh_token.refresh_token_id
    )
    _refresh_token_assignment = database.crud.add_to_database(_refresh_token_assignment, db_session)
    # Map the scopes to the token
    if scopes is None:
        # Use the scopes the user owns
        for scope in user.scopes:
            # Create a mapping entry
            _token_scope_mapping = database.tables.RefreshTokenToScopes(
                token_id=_token.token_id,
                scope_id=scope.scope_id
            )
            # Insert the mapping into the database
            database.crud.add_to_database(_token_scope_mapping, db_session)
    else:
        for scope_value in scopes:
            # Get the scope data from the database
            _scope = database.crud.get_scope_by_value(scope_value, db_session)
            # Check if the scope still exists
            if _scope is not None:
                # Create a mapping entry
                _token_scope_mapping = database.tables.RefreshTokenToScopes(
                    token_id=_refresh_token.refresh_token_id,
                    scope_id=_scope.scope_id
                )
                # Insert the mapping into the database
                database.crud.add_to_database(_token_scope_mapping, db_session)
    # Now generate the returned token set
    # Refresh the access token
    db_session.refresh(_token)
    # Build the scope string
    _scope_string = ""
    for scope in _token.scopes:
        _scope_string += f"{scope.scope_value} "
    _scope_string = _scope_string.strip()
    # Now return the TokenSet
    return models.outgoing.TokenSet(
        access_token=_token.token,
        expires_in=ACCESS_TOKEN_TTL,
        refresh_token=_refresh_token.refresh_token,
        scope=_scope_string
    )


def get_scopes_from_user(_user: database.tables.Account) -> list[str]:
    """Get a list of scope values from the account

    :param _user: The user account which shall be used
    :type _user: database.tables.Account
    :returns: A list of scope strings
    """
    _list = []
    for _allowed_scope in _user.scopes:
        _list.append(_allowed_scope.scope_value)
    return _list


def field_may_be_update_source(new_value: Optional[str]) -> bool:
    """Check if the field may be used for an update

    The check is done by testing if the str is actually None and stripping the string does not
    result in an empty string. This shall not be used for passwords, since those values may not
    be stripped of any whitespaces

    :param new_value: The value the field shall have after the update
    :return: True if the field may be used, False if it may not be used
    """
    if new_value is None:
        return False
    elif new_value.strip() == "":
        return False
    else:
        return True
