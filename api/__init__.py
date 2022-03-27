"""Module containing the routes and actions run when requesting a specific route"""
import logging
from threading import Thread
from typing import Optional, Union

import sqlalchemy.exc
from fastapi import Body, Depends, FastAPI as RESTApplication, Form, Security, Request
from fastapi.responses import UJSONResponse
from passlib.hash import pbkdf2_sha512 as pwd_hasher
from py_eureka_client.eureka_client import EurekaClient
from pydantic import SecretStr
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

import database
import models.shared
import security
import tools
from database import Scope, tables
from exceptions import AuthorizationException, ObjectNotFoundException
from models.http import incoming, outgoing
from settings import ServiceSettings, ServiceRegistrySettings
from . import dependencies, utilities

auth_service_rest = RESTApplication()
"""Main API application for this service"""

# Create a logger for the API and its routes
__logger = logging.getLogger('HTTP')
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
    # Enable the global usage of the service settings and the service registry client
    # pylint: disable=invalid-name, global-statement
    global __settings, __service_registry_client, _heartbeat_event, _heartbeat_thread
    # Read the settings
    __service_settings = ServiceSettings()
    _service_registry_settings = ServiceRegistrySettings()
    logging.basicConfig(
        format='%(levelname)-8s | %(asctime)s | %(name)-25s | %(message)s',
        level=tools.resolve_log_level(__service_settings.log_level)
    )
    __logger = logging.getLogger('HTTP.Startup')
    __logger.info("Starting the API")
    # Create a new service registry client
    __logger.info('Creating a new service registry client')
    _eureka_client_options = {
        'eureka_server':            f'http://{_service_registry_settings.host}:{_service_registry_settings.port}',
        'app_name':                 __service_settings.name,
        'instance_port':            __service_settings.http_port,
        'should_register':          True,
        'should_discover':          False,
        'renewal_interval_in_secs': 1,
        'duration_in_secs':         5
    }
    __logger.debug('Client Properties: %s', _eureka_client_options)
    __service_registry_client = EurekaClient(**_eureka_client_options)
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
    __log = logging.getLogger('HTTP.Shutdown')
    # Enable the global usage of the registry client
    # pylint: disable=invalid-name
    global __service_registry_client
    __log.info('Stopping the Registry Client')
    __service_registry_client.stop()
    __log.info('Shutdown Sequence completed')


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


@auth_service_rest.exception_handler(ObjectNotFoundException)
async def handle_object_not_found_exception(
        _request: Request,
        _exc: ObjectNotFoundException
) -> UJSONResponse:
    """Handle the ObjectNotFound exception

    :param _request: The request in which the exception occurred in
    :type _request: Request
    :param _exc: The ObjectNotFound Exception
    :type _exc: ObjectNotFoundException
    :return: A JSON response explaining the reason behind the error
    :rtype: UJSONResponse
    """
    return UJSONResponse(
        content={
            "error": "The requested object was not found. Please check your request"
        },
        status_code=status.HTTP_404_NOT_FOUND
    )


@auth_service_rest.exception_handler(sqlalchemy.exc.IntegrityError)
async def handle_integrity_error(
        _request: Request,
        _exc: sqlalchemy.exc.IntegrityError
):
    """Handle a sqlalchemy Integrity Error

    :param _request: The request in which the exception occurred
    :param _exc: The exception which was thrown
    :return:
    """
    return UJSONResponse(
        content={
            "error":             "DUPLICATE_ENTRY",
            "error_description": "The resource you tried to create already exists"
        },
        status_code=status.HTTP_409_CONFLICT
    )


# == OAuth2 Routes ==
# pylint: disable=too-many-branches
@auth_service_rest.post(
    path='/oauth/token',
    response_model=outgoing.TokenSet,
    response_model_exclude_none=True,
    response_model_by_alias=False
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
    else:
        raise AuthorizationException(
            short_error='invalid_request',
            error_description='There was no grant_type set',
            http_status_code=status.HTTP_400_BAD_REQUEST
        )


@auth_service_rest.post(
    path='/oauth/check_token',
    response_model=models.shared.TokenIntrospectionResult,
    response_model_exclude_none=True,
    response_model_by_alias=False
)
async def oauth_token_introspection(
        _active_user: tables.Account = Security(dependencies.get_current_user),
        db_session: Session = Depends(database.session),
        token: str = Form(...),
        scope: Optional[str] = Form(None)
) -> models.shared.TokenIntrospectionResult:
    """Run an introspection of a token to check its validity

    The check may be run as check for the general validity. It also may be run against one or
    more scopes which will return the validity for the scopes sent in the request

    :param _active_user: The user making the request (not used here but still needed)
    :param db_session: The database session
    :param token: The token on which an introspection shall be executed
    :param scope: The scopes against which the token shall be tested explicitly
    :return: The introspection response
    """
    return security.run_token_introspection(token, scope, db_session)


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
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    # Check if the token owner is also the requester
    if _access_token is not None and _access_token.user[0].account_id == _active_user.account_id:
        # Since it is the same person delete
        db_session.delete(_access_token)
        db_session.commit()
    if _refresh_token is not None and _refresh_token.user[0].account_id == _active_user.account_id:
        # Since it is the same person delete
        db_session.delete(_refresh_token)
        db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# == User operation Routes ==
@auth_service_rest.get(
    path='/users/me',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True,
    response_model_by_alias=False
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
    response_model_exclude_none=True,
    response_model_by_alias=False
)
async def user_update_own_account_password(
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["me"]),
        db_session: Session = Depends(database.session),
        old_password: SecretStr = Body(..., embed=True, alias="oldPassword"),
        new_password: SecretStr = Body(..., embed=True, alias="newPassword")
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
    # Remove all access tokens from the database for this user
    _assignments = (db_session
                    .query(tables.AccountToToken)
                    .filter(tables.AccountToToken.account_id == _active_user.account_id))
    for assignment in _assignments:
        database.crud.delete_access_token(assignment.token_id, db_session)
    # Remove all refresh tokens from the database for this user
    _assignments = (db_session
                    .query(tables.AccountToRefreshTokens)
                    .filter(tables.AccountToRefreshTokens.account_id == _active_user.account_id))
    for assignment in _assignments:
        database.crud.delete_refresh_token(assignment.refresh_token_id, db_session)
    # Commit those changes
    db_session.commit()
    # Return the user
    return _active_user


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
    _user = database.crud.get_user(user_id, db_session)
    if _user is None:
        raise ObjectNotFoundException
    return _user


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
    Use with caution. Calling this method will result in a logout of the affected user (even
    though no information has changed)

    :param user_id: The id of the user which shall be updated
    :param _active_user: The user making the request
    :param db_session: The database session used to manipulate the user
    :param update_info: The new account information
    :return: The updated account information
    """
    # Check if the to be manipulated user exists
    _user = database.crud.get_user(user_id, db_session)
    if _user is None:
        raise ObjectNotFoundException
    # Start manipulating the user
    if utilities.field_may_be_update_source(update_info.first_name):
        _user.first_name = update_info.first_name.strip()
    if utilities.field_may_be_update_source(update_info.last_name):
        _user.last_name = update_info.last_name.strip()
    if utilities.field_may_be_update_source(update_info.username):
        _user.username = update_info.username.strip()
    if update_info.password is not None and update_info.password.get_secret_value() != "":
        _user.password = pwd_hasher.hash(update_info.password.get_secret_value())
    if utilities.field_may_be_update_source(update_info.scopes):
        # Delete the old scope assignments
        (db_session
         .query(tables.AccountToScope)
         .filter(tables.AccountToScope.account_id == user_id)
         .delete())
        # Now assign the new scopes
        for scope in update_info.scopes.split():
            database.crud.map_scope_to_account(scope, _user.account_id, db_session)
    if update_info.roles is not None and len(update_info.roles) > 0:
        # Delete the old role assignments
        (db_session
         .query(tables.AccountToRoles)
         .filter(tables.AccountToRoles.account_id == user_id)
         .delete())
        # Now assign the new scopes
        for role in update_info.roles:
            database.crud.map_role_to_account(role, _user.account_id, db_session)
    if update_info.active is not None:
        _user.is_active = update_info.active
    # If any information was changed commit the changes and delete all tokens which are owned by
    # the user
    db_session.commit()
    # Remove all access tokens from the database for this user
    _assignments = (db_session
                    .query(tables.AccountToToken)
                    .filter(tables.AccountToToken.account_id == _user.account_id))
    for assignment in _assignments:
        database.crud.delete_access_token(assignment.token_id, db_session)
    # Remove all refresh tokens from the database for this user
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
    # Since no user was found return a 404 via the object not found exception
    raise ObjectNotFoundException


@auth_service_rest.get(
    path='/users',
    response_model=list[outgoing.UserAccount],
    response_model_exclude_none=True,
    response_model_by_alias=True
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
    return database.crud.get_all(tables.Account, db_session)


@auth_service_rest.put(
    path='/users',
    response_model=outgoing.UserAccount,
    response_model_exclude_none=True,
    response_model_by_alias=False,
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
    return database.crud.add_user(new_user, db_session)


# == Scope Operation Routes ==
@auth_service_rest.get(
    path='/scopes/{scope_id}',
    response_model=outgoing.Scope,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def scopes_get_scope_information(
        scope_id: int,
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
) -> Union[Response, Scope]:
    """Get information about a scope by its internal id

    :param scope_id: The internal id of the scope
    :param _active_user: The administrator making this request
    :param db_session: Database session used to retrieve the scope data
    :return: The requested scope if it was found
    """
    _scope = database.crud.get_scope(scope_id, db_session)
    if _scope is None:
        raise ObjectNotFoundException
    return _scope


@auth_service_rest.patch(
    path='/scopes/{scope_id}',
    response_model=outgoing.Scope,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def scopes_update_scope(
        scope_id: int,
        update_info: models.shared.ScopeUpdate = Body(...),
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
) -> tables.Scope:
    """Update an already present scope

    :param update_info: The update information for the scope
    :param scope_id: The id of the scope which shall be edited
    :param _active_user: The administrator making the request
    :param db_session: The session used to manipulate the database entry
    :return: The manipulated scope
    """
    _scope = database.crud.get_scope(scope_id, db_session)
    # Check if the scope is existent
    if _scope is None:
        raise ObjectNotFoundException
    # Start editing the scope
    if update_info.scope_name is not None and update_info.scope_name.strip() != "":
        _scope.scope_name = update_info.scope_name
    if update_info.scope_description is not None and update_info.scope_description.strip() != "":
        _scope.scope_description = update_info.scope_description
    if update_info.scope_value is not None and update_info.scope_value.strip() != "":
        _scope.scope_value = update_info.scope_value
    # Commit the changes and refresh the scope
    db_session.commit()
    db_session.refresh(_scope)
    # Return the refreshed scope
    return _scope


@auth_service_rest.delete(
    path='/scopes/{scope_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def scopes_delete(
        scope_id: int,
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
):
    """Remove a scope from the system

    Removing a scope from the system will also remove the scope from any token and user assigned
    to it at the deletion time

    :param scope_id: ID of the scope which shall be deleted
    :param _active_user: The administrator making the call
    :param db_session: The database session used for deleting the scope
    """
    _scope = database.crud.get_scope(scope_id, db_session)
    if _scope is None:
        raise ObjectNotFoundException
    db_session.delete(_scope)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_service_rest.get(
    path='/scopes',
    response_model=list[outgoing.Scope],
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def scopes_get_all(
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
) -> list[tables.Scope]:
    """Get a list of all scopes currently in the system

    :param _active_user: The user trying to make this request
    :param db_session: The database session used to retrieve all elements
    :return: A list of all scopes
    """
    return database.crud.get_all(tables.Scope, db_session)


@auth_service_rest.put(
    path='/scopes',
    response_model=outgoing.Scope,
    response_model_exclude_none=True,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED
)
async def scopes_add(
        new_scope: models.shared.Scope = Body(...),
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
):
    """Create a new Role in the database

    :param new_scope: The new scope which shall be created
    :param _active_user: The user making the request
    :param db_session: The session used to insert the new scope in the database
    :return: The inserted scope
    """
    return database.crud.add_scope(new_scope, db_session)


# == Role Operation Routes ==
@auth_service_rest.get(
    path='/roles/{role_id}',
    response_model=outgoing.Role,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def roles_get_information(
        role_id: int,
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
) -> tables.Role:
    """Retrieve information about a specific role

    :param role_id: The role which shall be returned
    :param _active_user: The user making the request
    :param db_session: The database session used to retrieve the role
    :return: The Role which was queried
    """
    _role = database.crud.get_role(role_id, db_session)
    if _role is None:
        raise ObjectNotFoundException
    return _role


@auth_service_rest.patch(
    path='/roles/{role_id}',
    response_model=outgoing.Role,
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def roles_update(
        role_id: int,
        update_info: incoming.RoleUpdate = Body(...),
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
) -> tables.Role:
    """Update a role

    :param role_id: The internal id of the role which shall be updated
    :param update_info: New information about the role
    :param _active_user: The user performing the update
    :param db_session: The database session used to manipulate the role
    :return: The manipulated role
    """
    # Try getting a role from the database
    _role = database.crud.get_role(role_id, db_session)
    if _role is None:
        raise ObjectNotFoundException
    if utilities.field_may_be_update_source(update_info.role_name):
        _role.role_name = update_info.role_name
    if utilities.field_may_be_update_source(update_info.role_description):
        _role.role_description = update_info.role_description
    if utilities.field_may_be_update_source(update_info.role_scopes):
        for _scope_value in update_info.role_scopes.split():
            # Remove all old mappings
            database.crud.clear_mapping_entries(tables.RoleToScope, role_id, db_session)
            database.crud.map_scope_to_role(_role.role_id, _scope_value, db_session)
    # Commit all changes
    db_session.commit()
    # Refresh the role
    db_session.refresh(_role)
    # Return the role
    return _role


@auth_service_rest.delete(
    path='/roles/{role_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
async def roles_delete(
        role_id: int,
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
):
    """Delete a role from the server

    :param role_id: The internal id of the role which shall be deleted
    :param _active_user: The user making the deletion request
    :param db_session: The database session used to delete the role
    """
    _role = database.crud.get_role(role_id, db_session)
    if _role is None:
        raise ObjectNotFoundException
    db_session.delete(_role)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_service_rest.get(
    path='/roles',
    response_model=list[outgoing.Role],
    response_model_exclude_none=True,
    response_model_by_alias=True
)
async def roles_get_all(
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
):
    """Get all roles present in the system

    :param _active_user:  The user making the request
    :param db_session: The database session used to get all roles
    :return:
    """
    return database.crud.get_all(tables.Role, db_session)


@auth_service_rest.put(
    path='/roles',
    response_model=outgoing.Role,
    response_model_exclude_none=True,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED
)
async def roles_add(
        new_role: incoming.Role = Body(...),
        _active_user: tables.Account = Security(dependencies.get_current_user, scopes=["admin"]),
        db_session: Session = Depends(database.session)
):
    """Add a new Role to the System

    :param new_role: The new role which shall be inserted
    :param _active_user: The user making the request
    :param db_session: The database session used to insert the role
    :return:
    """
    return database.crud.add_role(new_role, db_session)


@auth_service_rest.get(
    path='/',
)
async def status_route(_request: Request):
    """This route will always return a 204 as response code

    :param _request: A request object needed to be specified
    :return: A HTTP 204 Response indicating that the service is alive
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)
