import http
import logging
from http import HTTPStatus

import fastapi
import sqlalchemy.exc
import starlette.background

import database.crud
import database.tables
import exceptions
import models.common
import models.responses
import tools
from api import dependencies, handlers, utilities

# %% API Endpoints
oauth_api = fastapi.FastAPI()

# %% Handlers

oauth_api.add_exception_handler(exceptions.APIException, handlers.handle_api_error)
oauth_api.add_exception_handler(sqlalchemy.exc.IntegrityError, handlers.handle_integrity_error)
oauth_api.add_exception_handler(fastapi.exceptions.RequestValidationError, handlers.handle_request_validation_error)


# %% Routes
@oauth_api.post(path="/token")
async def oauth2_token(
    form: dependencies.OAuth2AuthorizationRequestForm = fastapi.Depends(use_cache=False),
):
    """
    OAuth2 Token Request

    Request a new pair of access and refresh tokens that may be used for authorizing

    \f

    :param form: The form data containing the login information
    :type form: dependencies.OAuth2AuthorizationRequestForm
    :return: A new pair of access and refresh tokens
    :rtype: JSON
    """
    if form.grant_type == "refresh_token":
        refresh_token = database.crud.get_refresh_token_data(form.refresh_token)
        if refresh_token is None:
            raise exceptions.APIException(
                error_code="WRONG_CREDENTIALS",
                error_name="Wrong Credentials",
                error_description="The supplied refresh_token is not valid",
                status_code=HTTPStatus.BAD_REQUEST,
            )
        # Get the owner of the id and check if the user is active
        user = database.crud.get_user_account(refresh_token.owner_id)
        if user is None:
            raise exceptions.APIException(
                error_code="WRONG_CREDENTIALS",
                error_name="Wrong Credentials",
                error_description="No user associated to this refresh token",
                status_code=HTTPStatus.BAD_REQUEST,
            )
        if not user.active:
            raise exceptions.APIException(
                error_code="ACCOUNT_DISABLED",
                error_name="User Account disabled",
                error_description="The user account associated to this refresh token is disabled.",
                status_code=HTTPStatus.FORBIDDEN,
            )
        refresh_token_scopes = database.crud.get_refresh_token_scopes(refresh_token)
        scope_string = " ".join([scope.scope_string_value for scope in refresh_token_scopes])
        token_set = utilities.generate_token_set(user, scope_string)
        tasks = starlette.background.BackgroundTasks()
        tasks.add_task(database.crud.insert_token_set, user=user, token_set=token_set)
        tasks.add_task(database.crud.delete_refresh_token, token=refresh_token)
        return fastapi.Response(content=token_set.json(), media_type="application/json", background=tasks)
    elif form.grant_type == "password":
        # Try to get back a user account
        user = database.crud.get_user_account(form.username)
        if user is None:
            raise exceptions.APIException(
                error_code="WRONG_CREDENTIALS",
                error_name="Wrong Credentials",
                error_description="The supplied username/password combination is not valid",
                status_code=HTTPStatus.BAD_REQUEST,
            )
        # Hash the password that has been sent in the request
        if not utilities.verify_password(form.password.get_secret_value(), user.password.get_secret_value()):
            raise exceptions.APIException(
                error_code="WRONG_CREDENTIALS",
                error_name="Wrong Credentials",
                error_description="The supplied username/password combination is not valid",
                status_code=HTTPStatus.BAD_REQUEST,
            )
        if not user.active:
            raise exceptions.APIException(
                error_code="ACCOUNT_DISABLED",
                error_name="User Account Disabled",
                error_description="The user account is currently deactivated",
                status_code=HTTPStatus.FORBIDDEN,
            )
        # Since the password matched the hash in the database create a new token set now
        token_set = utilities.generate_token_set(user, scopes=form.scopes)
        db_task = starlette.background.BackgroundTask(database.crud.insert_token_set, user=user, token_set=token_set)
        kong_task = starlette.background.BackgroundTask(
            tools.store_token_in_gateway, token_set=token_set, username=user.username
        )
        tasks = starlette.background.BackgroundTasks([db_task, kong_task])
        return fastapi.Response(content=token_set.json(), media_type="application/json", background=tasks)
    else:
        raise exceptions.APIException(
            error_code="UNSUPPORTED_GRANT_TYPE",
            error_name="Unsupported Grant Type",
            error_description="The supplied grant type either not supported or no grant type was set",
        )


@oauth_api.post(
    path="/check_token",
    response_model_exclude_none=True,
    response_model=models.responses.TokenIntrospection,
)
async def oauth2_check_token(
    _user: models.common.UserAccount = fastapi.Security(dependencies.get_authorized_user),
    token: str = fastapi.Form(default=..., alias="token"),
):
    # Get information about the two possible token types
    access_token_information = database.crud.get_access_token_data(token)
    refresh_token_information = database.crud.get_refresh_token_data(token)
    if access_token_information is not None and refresh_token_information is None:
        _s = [
                scope.scope_string_value for scope in database.crud.get_access_token_scopes(access_token_information)
            ]
        if "administration" in _s:
            scopes = [
                scope.scope_string_value for scope in database.crud.get_scopes()
            ]
        else:
            scopes = _s
        return models.responses.TokenIntrospection(
            active=access_token_information.active,
            scope=scopes,
            expires_at=access_token_information.expires.timestamp(),
            created_at=access_token_information.created.timestamp(),
            token_type="access_token",
        )
    elif access_token_information is None and refresh_token_information is not None:
        return models.responses.TokenIntrospection(
            active=refresh_token_information.active,
            scope=[
                scope.scope_string_value for scope in database.crud.get_refresh_token_scopes(refresh_token_information)
            ],
            expires_at=refresh_token_information.expires.timestamp(),
            token_type="refresh_token",
        )
    else:
        return models.responses.TokenIntrospection(active=False)


@oauth_api.post(path="/revoke")
async def oauth2_revoke(
    user: models.common.UserAccount = fastapi.Security(dependencies.get_authorized_user),
    token: str = fastapi.Form(...),
):
    access_token_information = database.crud.get_access_token_data(token)
    refresh_token_information = database.crud.get_refresh_token_data(token)
    if access_token_information is None and refresh_token_information is None:
        return fastapi.Response(status_code=HTTPStatus.NO_CONTENT)
    if access_token_information is not None:
        if access_token_information.owner_id != user.id:
            raise exceptions.APIException(
                error_code="MISSING_PRIVILEGES",
                error_name="Missing Privileges",
                error_description="The account used to access this resource does not have the privileges to revoke "
                "this token",
                status_code=http.HTTPStatus.FORBIDDEN,
            )
        else:
            db_task = starlette.background.BackgroundTask(
                database.crud.delete_access_token, token=access_token_information
            )
            delete_gateway_token = starlette.background.BackgroundTask(
                tools.revoke_token_in_gateway, access_token=access_token_information.value.get_secret_value()
            )
            tasks = starlette.background.BackgroundTasks([db_task, delete_gateway_token])
            return fastapi.Response(status_code=HTTPStatus.NO_CONTENT, background=tasks)
    if refresh_token_information is not None:
        if refresh_token_information.owner_id != user.id:
            raise exceptions.APIException(
                error_code="MISSING_PRIVILEGES",
                error_name="Missing Privileges",
                error_description="The account used to access this resource does not have the privileges to revoke "
                "this token",
                status_code=http.HTTPStatus.FORBIDDEN,
            )
        else:
            task = starlette.background.BackgroundTask(
                database.crud.delete_refresh_token, token=refresh_token_information
            )
            return fastapi.Response(status_code=HTTPStatus.NO_CONTENT, background=task)
    return fastapi.Response(status_code=HTTPStatus.NO_CONTENT)
