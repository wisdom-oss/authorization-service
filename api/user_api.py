import http
import typing
from http import HTTPStatus

import fastapi
import passlib.hash
import pydantic
import sqlalchemy.exc

import api.dependencies
import database.crud
import database.tables
import exceptions
import models.common
import models.requests
import models.responses

# %% API Setup
user_api = fastapi.FastAPI()
user_api.add_exception_handler(exceptions.APIException, api.handlers.handle_api_error)
user_api.add_exception_handler(sqlalchemy.exc.IntegrityError, api.handlers.handle_integrity_error)
user_api.add_exception_handler(
    fastapi.exceptions.RequestValidationError, api.handlers.handle_request_validation_error
)
user_api.add_event_handler("startup", api.handlers.api_startup)


@user_api.get(path="/me", response_model=models.responses.UserAccount)
async def get_account_information(
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["account"]
    ),
):
    scopes = database.crud.get_user_scopes(user)
    return models.responses.UserAccount(**user.dict(), scopes=scopes)


@user_api.patch(path="/me")
async def update_account_password(
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["account"]
    ),
    old_password: pydantic.SecretStr = fastapi.Body(default=..., embed=True, alias="oldPassword"),
    new_password: pydantic.SecretStr = fastapi.Body(default=..., embed=True, alias="newPassword"),
):
    if not passlib.hash.argon2.verify(
        old_password.get_secret_value(), user.password.get_secret_value()
    ):
        raise exceptions.APIException(
            error_code="IDENTITY_CONFIRMATION_FAILURE",
            error_name="Invalid Credentials presented",
            error_description="The password could not be changed since the users identity could not be confirmed",
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    # Hash the new password
    new_password_hash = passlib.hash.argon2.using(type="ID").hash(new_password.get_secret_value())
    user.password = pydantic.SecretStr(new_password_hash)
    database.crud.store_changed_user(user)
    database.crud.delete_all_access_tokens(user)
    database.crud.delete_all_refresh_tokens(user)
    return fastapi.Response(status_code=HTTPStatus.OK)


@user_api.get(path="/enable/{account_identification")
async def disable_user(
    account_identification: typing.Union[str, int],
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administrator"]
    ),
):
    requested_user = database.crud.get_user_account(account_identification)
    if requested_user is None:
        raise exceptions.APIException(
            error_code="USER_NOT_FOUND",
            error_name="User unavailable",
            error_description="The user you tried to access does not exist in the system",
            status_code=HTTPStatus.NOT_FOUND,
        )
    requested_user.active = True
    database.crud.store_changed_user(requested_user)
    requested_user = database.crud.get_user_account(requested_user.id)
    requested_user_scopes = database.crud.get_user_scopes(requested_user)
    return models.responses.UserAccount(**requested_user.dict(), scopes=requested_user_scopes)


@user_api.get(path="/disable/{account_identification")
async def disable_user(
    account_identification: typing.Union[str, int],
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administrator"]
    ),
):
    requested_user = database.crud.get_user_account(account_identification)
    if requested_user is None:
        raise exceptions.APIException(
            error_code="USER_NOT_FOUND",
            error_name="User unavailable",
            error_description="The user you tried to access does not exist in the system",
            status_code=HTTPStatus.NOT_FOUND,
        )
    requested_user.active = False
    database.crud.store_changed_user(requested_user)
    requested_user = database.crud.get_user_account(requested_user.id)
    requested_user_scopes = database.crud.get_user_scopes(requested_user)
    return models.responses.UserAccount(**requested_user.dict(), scopes=requested_user_scopes)


@user_api.get(path="/{account_identification}")
async def get_user_information(
    account_identification: typing.Union[str, int],
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administrator"]
    ),
):
    requested_user = database.crud.get_user_account(account_identification)
    if requested_user is None:
        raise exceptions.APIException(
            error_code="USER_NOT_FOUND",
            error_name="User unavailable",
            error_description="The user you tried to access does not exist in the system",
            status_code=HTTPStatus.NOT_FOUND,
        )
    requested_user_scopes = database.crud.get_user_scopes(requested_user)
    return models.responses.UserAccount(**requested_user.dict(), scopes=requested_user_scopes)


@user_api.patch(path="/{account_identification}")
async def update_account_information(
    account_identification: typing.Union[str, int],
    new_account_information: models.requests.AccountUpdateInformation = fastapi.Body(...),
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administrator"]
    ),
):
    requested_account = database.crud.get_user_account(account_identification)
    # Now update the information if needed
    requested_account.first_name = (
        new_account_information.first_name
        if new_account_information.first_name is not None
        else requested_account.first_name
    )
    requested_account.last_name = (
        new_account_information.last_name
        if new_account_information.last_name is not None
        else requested_account.last_name
    )
    requested_account.username = (
        new_account_information.username
        if new_account_information.username is not None
        else requested_account.username
    )
    requested_account.password = (
        pydantic.SecretStr(
            passlib.hash.argon2.using(type="ID").hash(
                new_account_information.password.get_secret_value()
            )
        )
        if new_account_information.password is not None
        else requested_account.password
    )
    # Store the new information about the user
    database.crud.store_changed_user(requested_account)
    # Check if the scopes shall be changed
    if not new_account_information.keep_old_scopes:
        if new_account_information.scopes is None:
            raise exceptions.APIException(
                "INVALID_SCOPE_UPDATE_REQUESTED",
                "Missing Scope Data",
                "The update request indicated a update in the scopes, but no scopes have been sent",
                http.HTTPStatus.BAD_REQUEST,
            )
        new_scopes = [database.crud.get_scope(scope) for scope in new_account_information.scopes]
        if None in new_scopes:
            raise exceptions.APIException(
                "INVALID_SCOPE_UPDATE_REQUESTED",
                "Invalid Scope Requested",
                "You tried set a scope which is not available in the system",
                http.HTTPStatus.BAD_REQUEST,
            )
        if len(new_scopes) > 0:
            database.crud.set_user_scopes(requested_account, new_scopes)
    # Request the new user information
    requested_account = database.crud.get_user_account(requested_account.id)
    requested_account_scopes = database.crud.get_user_scopes(requested_account)
    # Since some information about the account has been changed, which may include the scopes. Remove all tokens this
    # user has
    database.crud.delete_all_access_tokens(requested_account)
    database.crud.delete_all_refresh_tokens(requested_account)
    return models.responses.UserAccount(**requested_account.dict(), scopes=requested_account_scopes)


@user_api.delete(path="/{account_identification}")
async def delete_user(
    account_identification: typing.Union[str, int],
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administrator"]
    ),
):
    requested_account = database.crud.get_user_account(account_identification)
    if requested_account is None:
        raise exceptions.APIException(
            error_code="USER_NOT_FOUND",
            error_name="User unavailable",
            error_description="The user you tried to access does not exist in the system",
            status_code=HTTPStatus.NOT_FOUND,
        )
    database.crud.delete_user(requested_account)
    return fastapi.Response(status_code=HTTPStatus.NO_CONTENT)


@user_api.put(path="/new")
async def new_user(
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administrator"]
    ),
    new_account_information: models.requests.AccountCreationInformation = fastapi.Body(...),
):
    database.crud.store_new_user(new_account_information)
    new_account = database.crud.get_user_account(new_account_information.username)
    new_account_scopes = [
        database.crud.get_scope(scope) for scope in new_account_information.scopes
    ]
    if len(new_account_scopes) > 0:
        database.crud.set_user_scopes(new_account, new_account_scopes)
    new_account_scopes = database.crud.get_user_scopes(new_account)
    return models.responses.UserAccount(**new_account.dict(), scopes=new_account_scopes)


@user_api.get(path="/")
async def get_users(
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administrator"]
    )
):
    return database.crud.get_user_accounts()
