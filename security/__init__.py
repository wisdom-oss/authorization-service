"""Security related tools which will be used to validate tokens"""
import time

from sqlalchemy.orm import Session
from passlib.hash import argon2


import database
from database import tables
from models.shared import TokenIntrospectionResult


def client_credentials_valid(
        client_id: str,
        client_secret: str,
        session: Session = next(database.session())
) -> bool:
    """Check if the supplied client credentials match and are valid

    :param session: The database session used to retrieve the database content
    :param client_id: The client id
    :param client_secret: The client secret
    :return: True if the client id/secret combination match those on record
    """
    # Try to get a database entry for the client_id
    _client_credentials = database.crud.get_client_credential_by_client_id(client_id, session)
    # Check if the query returned anything
    if _client_credentials is None:
        return False
    # Use the hashing method to validate if the client secret matches the one on the server and
    # return the result since a client credential allows the full access to the amqp interface
    return argon2.verify(client_secret, _client_credentials.client_secret)


def run_token_introspection(
        token: str,
        scope: str,
        session: Session = next(database.session())
) -> TokenIntrospectionResult:
    """Execute a token introspection and return the result of the introspection

    :param token: The token which shall be introspected
    :param scope: The scopes against which the token shall be tested
    :param session: The database session which is used to access the data
    :return: A TokenIntrospectionResult
    :rtype: TokenIntrospectionResult
    """
    # Check both tables for a token
    _access_token = database.crud.get_access_token_by_token(token, session)
    _refresh_token = database.crud.get_refresh_token_by_token(token, session)
    # Check if any of the values is None
    if all(_token is None for _token in [_access_token, _refresh_token]):
        # Return that the token is not active
        return TokenIntrospectionResult(active=False)
    # Assign the token which was found to the working token object
    _token = next((_t for _t in [_access_token, _refresh_token] if _t is not None), None)
    # Check if the assignment is not None
    if _token is None:
        return TokenIntrospectionResult(active=False)
    # Check if the token has already expired
    if time.time() >= _token.expires:
        return TokenIntrospectionResult(active=False)
    # Check if the user assigned to the token is not disabled
    if not _token.user[0].is_active:
        return TokenIntrospectionResult(active=False)
    # Create a list of the scopes assigned to the token
    _scopes = [_scope.scope_value for _scope in _token.scopes]
    # Check if scopes were supplied to the function
    if scope is not None and len(scope.split()) > 0:
        # Since scopes were supplied to the function we now will check if any scope supplied to
        # the function is not in the scopes of the token
        if any(_scope not in _scopes for _scope in scope.split()):
            return TokenIntrospectionResult(active=False)
    # Return the result of the introspection
    return TokenIntrospectionResult(
        active=True,
        # Use the supplied scopes if any were supplied
        scopes=scope if scope is not None and len(scope.split()) > 0 else ' '.join(_scopes),
        username=_token.user[0].username,
        # Set the token type according to the type of the token
        token_type='access_token' if isinstance(_token, tables.AccessToken) else 'refresh_token',
        exp=_token.expires,
        # Set the creation time if a access token was introspected
        iat=_token.created if isinstance(_token, tables.AccessToken) else None
    )