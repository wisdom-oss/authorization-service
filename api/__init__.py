"""Module containing the routes and actions run when requesting a specific route"""
import logging
import time
from typing import Optional, Union

import sqlalchemy.exc
from fastapi import Body, Depends, FastAPI as fastapi_application, Form, Security
from fastapi import Request
from fastapi.responses import UJSONResponse
from passlib.hash import pbkdf2_sha512 as pwd_hasher
from py_eureka_client.eureka_client import EurekaClient
from pydantic import SecretStr
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

import database
from database import tables
from exceptions import AuthorizationException
from models import ServiceSettings, incoming, outgoing
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
    __log = logging.getLogger('API.shutdown')
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


# == User operation Routes ==
@auth_service_rest.get(
    path='/users/me',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True
)
async def users_get_own_account_info(
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["me"])
) -> outgoing.UserAccount:
    """Get information about the authorized user making this request

    :param _active_user: The user making the request
    :return: The account information
    """
    return outgoing.UserAccount.from_orm(_active_user)


@auth_service_rest.patch(
    path='/users/me',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True
)
async def user_update_own_account_password(
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["me"]),
        db_session: Session = Depends(database.session),
        old_password: SecretStr = Body(..., embed=True),
        new_password: SecretStr = Body(..., embed=True)
) -> outgoing.UserAccount:
    """Allow the current user to update the password assigned to the account

    :param _active_user: The user whose password shall be updated
    :param db_session: Database connection used for changing the password
    :param old_password: The old password needed for confirming the password change
    :param new_password: The new password which shall be set
    :return: The account after the password change
    """
    # Check if the old password matches the one on record
    if not pwd_hasher.verify(old_password.get_secret_value(), _active_user.password):
        raise AuthorizationException(
            short_error='invalid_grant',
            error_description='The password confirmation did not match the password on record',
            http_status_code=status.HTTP_403_FORBIDDEN
        )
    # Now update the password
    _active_user.password = pwd_hasher.hash(new_password.get_secret_value())
    # Now commit the changes in the database
    db_session.commit()
    # Now refresh the user account
    db_session.refresh(_active_user)
    # Return the user
    return outgoing.UserAccount.from_orm(_active_user)


@auth_service_rest.get(
    path='/users/{user_id}',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def users_get_user_information(
        user_id: int,
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
) -> outgoing.UserAccount:
    """Get information about a specific user account by its internal id

    :param user_id: The internal account id
    :param _active_user: The user making the request
    :param db_session: The database session for retrieving the account data
    :return: The account data
    """
    return database.crud.get_user(user_id, db_session)


@auth_service_rest.patch(
    path='/users/{user_id}',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def users_update_user_information(
        user_id: int,
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session),
        update_info: incoming.UserUpdate = Body(...)
) -> Union[outgoing.UserAccount, Response]:
    """Update a users account information

    Since this is an admin endpoint no additional verification is necessary to change passwords.
    Use with caution

    :param user_id: The id of the user which shall be updated
    :param _active_user: The user making the request
    :param db_session: The database session used to manipulate the user
    :param update_info: The new account information
    :return: The updated account information
    """
    # Check if the to be manipulated user exists
    _user = database.crud.get_user(user_id, db_session)
    if _user is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    # Save if anything was changed to remove all access and refresh tokens to ensure a reload of the
    # data later on
    _information_changed = False
    # Start manipulating the user
    if update_info.first_name is not None and update_info.first_name.strip() != "":
        _information_changed = True
        _user.first_name = update_info.first_name.strip()
    if update_info.last_name is not None and update_info.last_name.strip() != "":
        _information_changed = True
        _user.last_name = update_info.last_name.strip()
    if update_info.username is not None and update_info.username.strip() != "":
        _information_changed = True
        _user.username = update_info.username.strip()
    if update_info.password is not None and update_info.password.get_secret_value() != "":
        _information_changed = True
        _user.password = pwd_hasher.hash(update_info.password.get_secret_value())
    if update_info.scopes is not None and update_info.scopes.strip() != "":
        # Delete the old scope assignments
        (db_session
         .query(tables.AccountToScope)
         .filter(tables.AccountToScope.account_id == user_id)
         .delete())
        # Now assign the new scopes
        for scope in update_info.scopes.split():
            database.crud.map_scope_to_account(scope, _user.account_id, db_session)
        _information_changed = True
    if update_info.roles is not None and len(update_info.roles) > 0:
        # Delete the old role assignments
        (db_session
         .query(tables.AccountToRoles)
         .filter(tables.AccountToRoles.account_id == user_id)
         .delete())
        # Now assign the new scopes
        for role in update_info.roles:
            database.crud.map_role_to_account(role, _user.account_id, db_session)
        _information_changed = True
    # If any information was changed commit the changes and delete all tokens which are owned by
    # the user
    if _information_changed:
        db_session.commit()
        # Remove all access token assignments from the database
        _assignments = (db_session
                        .query(tables.AccountToToken)
                        .filter(tables.AccountToToken.account_id == _user.account_id))
        for assignment in _assignments:
            database.crud.delete_access_token(assignment.token_id, db_session)
        # Remove all refresh token assignments from the database
        _assignments = (db_session
                        .query(tables.AccountToRefreshTokens)
                        .filter(tables.AccountToRefreshTokens.account_id == _user.account_id))
        for assignment in _assignments:
            database.crud.delete_refresh_token(assignment.refresh_token_id, db_session)
        # Commit those changes
        db_session.commit()
        # Refresh the changed user
        db_session.refresh(_user)
    return _user


@auth_service_rest.delete(
    path='/users/{user_id}'
)
async def users_delete(
        user_id: int,
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
):
    """Delete a user by its internal id

    :param user_id: Account ID of the account which shall be deleted
    :param _active_user: Currently active user
    :param db_session: Database session
    :return: A `200 OK` response if the user was deleted. If the user was not found 404
    """
    # Try getting a user from the database
    _user = database.crud.get_user(user_id, db_session)
    # If a user was found delete it
    if isinstance(_user, tables.Account):
        db_session.delete(_user)
        db_session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    # Since no user was found return a 404
    return Response(status_code=status.HTTP_404_NOT_FOUND)


@auth_service_rest.get(
    path='/users',
    response_model=list[outgoing.UserAccount],
    response_model_exclude_none=True
)
async def users_get_all(
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
):
    """Get a list of all user accounts

    :param _active_user:
    :param db_session:
    :return:
    """
    return db_session.query(tables.Account).all()


@auth_service_rest.put(
    path='/users',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED
)
async def users_add(
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session),
        new_user: incoming.NewUserAccount = Body(...)
):
    """Add a user to the database

    :param _active_user: The user making the request
    :param db_session: The session used to insert the new user
    :param new_user: The new user to be inserted
    :return:
    """
    # Try inserting the new user
    try:
        _user = database.crud.add_user(new_user, db_session)
        return _user
    except sqlalchemy.exc.IntegrityError:
        return Response(status_code=status.HTTP_409_CONFLICT)
