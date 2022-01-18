"""Package containing some custom dependencies for the API application"""
import time

from fastapi import Depends, Form
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import SecretStr
from sqlalchemy.orm import Session
from starlette import status

import models.outgoing
from database import session, crud, tables
from exceptions import AuthorizationException

__oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='oauth/token',
    scheme_name='WISdoM Central Authorization',
    auto_error=False
)


async def get_current_user(
        security_scopes: SecurityScopes,
        token: str = Depends(__oauth2_scheme),
        db_session: Session = Depends(session)
) -> tables.Account:
    """Resolve and check permissions for the current user via the given access token

    :param security_scopes: Scopes which are needed for accessing the endpoint
    :param token: Bearer Token
    :param db_session: Database session
    :return: The currently active account
    """
    # Check if the token was set during the request
    if token in (None, "undefined"):
        raise AuthorizationException(
            short_error="invalid_request",
            error_description='No Bearer token present in the request',
            http_status_code=status.HTTP_400_BAD_REQUEST
        )
    # Try to retrieve the data of the token
    token_data = crud.get_access_token_by_token(token, db_session)
    # Check if the token is legitimate by checking if the retrieval returned None
    if token_data is None:
        raise AuthorizationException(
            short_error='invalid_token',
            http_status_code=status.HTTP_401_UNAUTHORIZED
        )
    # Check if the token was not disabled
    if not token_data.active:
        raise AuthorizationException(
            short_error='invalid_token',
            http_status_code=status.HTTP_401_UNAUTHORIZED
        )
    # Check if the tokens ttl has expired
    if time.time() >= token_data.expires:
        raise AuthorizationException(
            short_error='invalid_token',
            http_status_code=status.HTTP_401_UNAUTHORIZED
        )
    # Check if the token is live already
    if time.time() <= token_data.created:
        raise AuthorizationException(
            short_error='invalid_token',
            http_status_code=status.HTTP_401_UNAUTHORIZED
        )
    _user: tables.Account = token_data.user[0]
    if not _user.is_active:
        raise AuthorizationException(
            short_error='invalid_token',
            http_status_code=status.HTTP_401_UNAUTHORIZED
        )
    # Create a list of token scope values
    _token_scopes = []
    for _token_scope in token_data.scopes:
        _token_scopes.append(_token_scope.scope_value)
    # Check if any of the needed scopes is in the tokens scopes
    for needed_scope in security_scopes.scopes:
        if needed_scope not in _token_scopes:
            raise AuthorizationException(
                short_error='insufficient_scope',
                http_status_code=status.HTTP_401_UNAUTHORIZED,
                optional_data=f"scope={security_scopes.scope_str}"
            )
    # Now return the database orm user
    return _user


class OAuth2AuthorizationRequestForm:
    # pylint: disable=too-few-public-methods

    """
    This dependency will create the following Form request parameters in the endpoint using it

    grant_type: The grant type used to obtain a new access and refresh token. Allowed values are
    either "password" or "refresh_token". Other grant types are not supported by this form

    username:   The username used to obtain a new token set (Required if the grant type is
    "password", must not be sent if the grant_type is set to "refresh_token")

    password:   The password used to obtain a new token set (Required if the grant type is
    "password", must not be sent if the grant_type is set to "refresh_token")

    refresh_token: The refresh token used to obtain a new token set (Required if grant type is
    "refresh_token", must not be sent if the grant_type is set to "password")
    """

    def __init__(
            self,
            grant_type: str = Form(None, regex="(?:^password$|^refresh_token$)"),
            username: str = Form(None, min_length=1),
            password: SecretStr = Form(None, min_length=1),
            refresh_token: str = Form(
                None,
                regex="[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
            ),
            scope: str = Form("")
    ):
        """Initialize the new OAuth2AuthorizationRequestForm

        If you protect an endpoint with this form you may not pass the following form data:

        Using "password" as grant_type -> "refresh_token"
        Using "refresh_token" as grant_type -> "username", "password"

        The refresh tokens format is automatically validated using a regex.

        :param grant_type: Grant type (supported values: "password", "refresh_token")
        :type grant_type: str
        :param username: Username of the account
        :type username: str
        :param password: Password of the account
        :type password: SecretStr
        :param refresh_token: Refresh token issued by a different request
        :type refresh_token: str
        :param scope: Scope string
        :type scope: str
        """
        # Save the gant type
        self.grant_type = grant_type
        # Check if the grant type is password
        if self.grant_type == 'password':
            # Check if the username and password are present in the request
            if None in (username, password) or refresh_token is not None:
                raise AuthorizationException(
                    short_error='invalid_request',
                    error_description='Supplying a refresh_token during a "password" grant is not '
                                      'allowed',
                    http_status_code=status.HTTP_400_BAD_REQUEST
                )
            # Save the username and password after passing this check
            self.username = username
            self.password = password
        if self.grant_type == 'refresh_token':
            if refresh_token is None or None not in (username, password):
                raise AuthorizationException(
                    short_error='invalid_request',
                    error_description='Supplying a username or password during a "refresh_token" '
                                      'grant is not allowed',
                    http_status_code=status.HTTP_400_BAD_REQUEST
                )
            # Save the refresh token after passing this check
            self.refresh_token = refresh_token
        # Save the scopes to the form
        self.scopes = scope
