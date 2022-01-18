"""Module containing the routes and actions run when requesting a specific route"""
import logging
import time
from typing import Optional, Union

from fastapi import Depends, FastAPI as fastapi_application, Form, Security
from fastapi import Request
from fastapi.responses import UJSONResponse
from passlib.hash import pbkdf2_sha512 as pwd_hasher
from py_eureka_client.eureka_client import EurekaClient
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

import database
from database import tables
from exceptions import AuthorizationException
from models import ServiceSettings, outgoing
from . import dependencies, utilities

auth_service_rest = fastapi_application()
"""Main API application for this service"""

# Create a logger for the API and its routes
__logger = logging.getLogger('API')
# Get the service settings
__settings: Optional[ServiceSettings] = None
# Create a service registry client
__service_registry_client: Optional[EurekaClient] = None


# == Event handlers == #
@auth_service_rest.on_event('startup')
def api_startup():
    """Event handler for the startup.

    The code will be executed before any HTTP incoming will be accepted
    """
    # Configure Logging to force using the info level
    logging.basicConfig(
        level=logging.INFO,
        force=True
    )
    # Get a logger for this event
    __log = logging.getLogger('API.startup')
    # Enable the global usage of the service settings and the service registry client
    global __settings, __service_registry_client  # pylint: disable=invalid-name, global-statement
    # Read the settings
    __settings = ServiceSettings()
    # Create a new service registry client
    __service_registry_client = EurekaClient(
        eureka_server=__settings.service_registry_url,
        app_name='wisdom-oss_authorization-service',
        instance_port=5000,
        should_register=True,
        should_discover=False,
        renewal_interval_in_secs=5,
        duration_in_secs=10
    )
    # Start the registry client
    __service_registry_client.start()
    # Set the status of this service to starting to disallow routing to them
    __service_registry_client.status_update('STARTING')
    # Initialize the database models and connections and check for any errors in the database tables
    database.initialise_databases()
    # Inform the service registry of the new server status
    __service_registry_client.status_update('UP')


@auth_service_rest.on_event('shutdown')
def api_shutdown():
    # pylint: disable=global-variable-not-assigned
    """Event handler for the shutdown process of the application"""
    # Get a logger for this event
    __log = logging.getLogger('API.startup')
    # Enable the global usage of the registry client
    global __service_registry_client  # pylint: disable=invalid-name
    # Stop the client and deregister the service
    __service_registry_client.stop()


# == Exception handlers ==
@auth_service_rest.exception_handler(AuthorizationException)
async def handle_authorization_exception(
        _request: Request,
        exc: AuthorizationException
) -> UJSONResponse:
    """Handle the Authorization exception

    This handler will set the error information according to the data present in the exception.
    Furthermore, the optional data will be passed in the `WWW-Authenticate` header.

    :param _request: The request in which the exception occurred in
    :type _request: Request
    :param exc: The Authorization Exception
    :type exc: AuthorizationException
    :return: A JSON response explaining the reason behind the error
    :rtype: UJSONResponse
    """
    _content = {
            "error":             exc.short_error,
            "error_description": exc.error_description
        }
    if exc.error_description is None:
        _content.pop("error_description")
    return UJSONResponse(
        status_code=exc.http_status_code,
        content=_content,
        headers={
            'WWW-Authenticate': f'Bearer {exc.optional_data}'.strip()
        }
    )


# == OAuth2 Routes ==
@auth_service_rest.post(
    path='/oauth/token',
    response_model=outgoing.TokenSet,
    response_model_exclude_none=True
)
async def oauth_login(
        form: dependencies.OAuth2AuthorizationRequestForm = Depends(),
        db_session: Session = Depends(database.session)
) -> outgoing.TokenSet:
    """Try to receive a token set with either username/password credentials or a refresh token

    :param form: Authorization Request Data
    :type form: OAuth2AuthorizationRequestForm
    :param db_session: Database session needed to validate the request data
    :type db_session: Session
    :return: Token Set
    :rtype: outgoing.TokenSet
    :raises exceptions.AuthorizationException: The request failed due to an error
        during the users authorization
    """
    # Check which type of grant is used
    if form.grant_type == 'password':
        # Get the user which is trying to log in from the database
        _user = database.crud.get_user_by_username(form.username, db_session)
        # Check if the user exists by checking the return of the database call
        if _user is None:
            # Raise an error since the user does not exist in the database
            raise AuthorizationException(
                short_error='invalid_grant',
                error_description='The supplied username/password combination is not valid',
                http_status_code=status.HTTP_400_BAD_REQUEST
            )
        # Try to verify the hashed password against the received password
        if not pwd_hasher.verify(form.password.get_secret_value(), _user.password) or \
                not _user.is_active:
            raise AuthorizationException(
                short_error='invalid_grant',
                error_description='The supplied username/password combination is not valid',
                http_status_code=status.HTTP_400_BAD_REQUEST
            )
        # Since the user passed all tests now the requested scopes will be checked against those
        # assigned to the account

        if form.scopes.strip() != "":
            # Check if the user has the privileges to use the requested scopes
            # Split the scope string to get the single scope values
            _requested_scopes = form.scopes.split()
            # Generate a list of scopes which the user may use
            _allowed_scopes = utilities.get_scopes_from_user(_user)
            # Now validate the requested scopes against that list
            if any(_scope not in _allowed_scopes for _scope in _requested_scopes):
                raise AuthorizationException(
                    short_error='invalid_scope',
                    http_status_code=status.HTTP_400_BAD_REQUEST
                )
            # Generate a token set
            return utilities.generate_token_set(
                _user,
                scopes=_requested_scopes,
                db_session=db_session
            )
        return utilities.generate_token_set(_user, db_session=db_session)
    elif form.grant_type == 'refresh_token':
        # Get the data of the refresh token
        _refresh_token = database.crud.get_refresh_token_by_token(form.refresh_token, db_session)
        # Check if the tokens exists
        if _refresh_token is None:
            raise AuthorizationException(
                short_error='invalid_request',
                http_status_code=status.HTTP_400_BAD_REQUEST
            )
        # Access the user and check if the user is active
        if not _refresh_token.user[0].is_active:
            raise AuthorizationException(
                short_error='invalid_grant',
                http_status_code=status.HTTP_400_BAD_REQUEST
            )
        # Iterate through the scopes which were assigned to the refresh token and check if the
        # and create a list of those for checking later if those are the same as the ones requested
        _allowed_scopes = []
        for scope in _refresh_token.scopes:
            _allowed_scopes.append(scope.scope_value)
        # Check if any scopes were requested explicitly
        if form.scopes.strip() != "":
            # Check if all requested scopes are in the original scopes
            if any(_r_scope not in _allowed_scopes for _r_scope in form.scopes.split()):
                raise AuthorizationException(
                    short_error='invalid_request',
                    error_description='The requested scopes do not match those originally '
                                      'issued with this refresh token',
                    http_status_code=status.HTTP_400_BAD_REQUEST
                )
            if any(_o_scope not in form.scopes.split() for _o_scope in _allowed_scopes):
                raise AuthorizationException(
                    short_error='invalid_request',
                    error_description='The requested scopes do not match those originally '
                                      'issued with this refresh token',
                    http_status_code=status.HTTP_400_BAD_REQUEST
                )
        # Since all tests were passed generate a new token set and remove the old refresh token
        db_session.delete(_refresh_token)
        db_session.commit()
        return utilities.generate_token_set(_refresh_token.user[0], db_session, _allowed_scopes)


@auth_service_rest.post(
    path='/oauth/check_token',
    response_model=outgoing.TokenIntrospection,
    response_model_exclude_none=True
)
async def oauth_token_introspection(
        _active_user: tables.Account = Security(dependencies.get_current_user),
        db_session: Session = Depends(database.session),
        token: str = Form(...),
        scope: Optional[str] = Form(None)
) -> outgoing.TokenIntrospection:
    """Run an introspection of a token to check its validity

    The check may be run as check for the general validity. It also may be run against one or
    more scopes which will return the validity for the scopes sent in the request

    :param _active_user: The user making the request (not used here but still needed)
    :param db_session: The database session
    :param token: The token on which an introspection shall be executed
    :param scope: The scopes against which the token shall be tested explicitly
    :return: The introspection response
    """
    # Receive the token data from both_tables
    _access_token_data = database.crud.get_access_token_by_token(token, db_session)
    _refresh_token_data = database.crud.get_refresh_token_by_token(token, db_session)
    _token_data: Union[tables.AccessToken, tables.RefreshToken]
    if _access_token_data is not None and _refresh_token_data is None:
        _token_data = _access_token_data
    elif _access_token_data is None and _refresh_token_data is not None:
        _token_data = _refresh_token_data
    else:
        return outgoing.TokenIntrospection(
            active=False
        )
    # Now check if the token has expired
    if time.time() >= _token_data.expires or not _token_data.user[0].is_active:
        return outgoing.TokenIntrospection(
            active=False
        )
    # Now check if the token is an access token and the active state is set correctly
    if isinstance(_token_data, database.tables.AccessToken) and not _token_data.active:
        return outgoing.TokenIntrospection(
            active=False
        )
    # Create a list of scope values associated to the token
    _token_scopes: list[str] = []
    for _token_scope in _token_data.scopes:
        _token_scopes.append(_token_scope.scope_value)
    # Now check if the scope string was set and has any content
    if scope is not None and scope.strip() != "":
        # Now iterate though the scopes in the scope string anc check if the scopes are in the
        # tokens scope.
        if any(_scope not in _token_scopes for _scope in scope.split()):
            return outgoing.TokenIntrospection(
                active=False
            )
        # All scopes which were queried are in the tokens scopes therefore return a complete
        # introspection response
        return outgoing.TokenIntrospection(
            active=True,
            scope=scope,
            username=_token_data.user[0].username,
            token_type='access_token',
            exp=_token_data.expires,
            iat=_token_data.created if isinstance(_token_data, tables.AccessToken) else None
        )
    return outgoing.TokenIntrospection(
        active=True,
        scope=' '.join(_token_scopes),
        username=_token_data.user[0].username,
        token_type='access_token',
        exp=_token_data.expires,
        iat=_token_data.created if isinstance(_token_data, tables.AccessToken) else None
    )


@auth_service_rest.post(
    path='/oauth/revoke',
    status_code=200
)
async def oauth_revoke_token(
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["me"]),
        db_session: Session = Depends(database.session),
        token: str = Form(...)
):
    """Revoke any type of token

    The revocation request will always be answered by an HTTP Code 200 code. Even if the token
    was not found.

    :param _active_user: The user making the request
    :param db_session: The database session
    :param token: The token which shall be revoked
    :return:
    """
    # Try getting a token from both types
    _access_token = database.crud.get_access_token_by_token(token, db_session)
    _refresh_token = database.crud.get_refresh_token_by_token(token, db_session)
    # Check any of the tokens were found
    if not any([isinstance(_access_token, tables.AccessToken), isinstance(
            _refresh_token, tables.RefreshToken)]):
        return Response(status_code=status.HTTP_200_OK)
    # Check if the token owner is also the requester
    if _access_token is not None and _access_token.user[0].account_id == _active_user.account_id:
        # Since it is the same person delete
        db_session.delete(_access_token)
        db_session.commit()
    if _refresh_token is not None and _refresh_token.user[0].account_id == _active_user.account_id:
        # Since it is the same person delete
        db_session.delete(_refresh_token)
        db_session.commit()
    return Response(status_code=status.HTTP_200_OK)
