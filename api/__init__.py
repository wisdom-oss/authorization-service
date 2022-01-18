"""Module containing the routes and actions run when requesting a specific route"""
import logging
from typing import Optional

from fastapi import Depends, FastAPI as fastapi_application
from fastapi import Request
from fastapi.responses import UJSONResponse
from passlib.hash import pbkdf2_sha512 as pwd_hasher
from py_eureka_client.eureka_client import EurekaClient
from sqlalchemy.orm import Session
from starlette import status

import database
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
    return UJSONResponse(
        status_code=exc.http_status_code,
        content={
            "error":             exc.short_error,
            "error_description": exc.error_description
        },
        headers={
            'WWW-Authenticate': f'Bearer {exc.optional_data}'.strip()
        }
    )


# == Login Routes ==
@auth_service_rest.post(
    path='/oauth/token',
    response_model=outgoing.TokenSet
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
