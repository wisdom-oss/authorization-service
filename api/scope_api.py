import typing
from http import HTTPStatus

import fastapi.requests
import sqlalchemy.exc

import api.handlers
import api.dependencies
import database.crud
import exceptions
import models.common
import models.requests


# %% API Setup
scope_api = fastapi.FastAPI()
scope_api.add_exception_handler(exceptions.APIException, api.handlers.handle_api_error)
scope_api.add_exception_handler(sqlalchemy.exc.IntegrityError, api.handlers.handle_integrity_error)
scope_api.add_exception_handler(
    fastapi.exceptions.RequestValidationError, api.handlers.handle_request_validation_error
)
scope_api.add_event_handler("startup", api.handlers.api_startup)


# %% Routes
@scope_api.get("/{scope_identifier}")
async def get_scope_information(
    scope_identifier: typing.Union[str, int],
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administration"]
    ),
):
    requested_scope = database.crud.get_scope(scope_identifier)
    if requested_scope is None:
        raise exceptions.APIException(
            error_code="SCOPE_NOT_FOUND",
            error_name="Scope unavailable",
            error_description="The scope you tried to access does not exist in the system",
            status_code=HTTPStatus.NOT_FOUND,
        )
    return requested_scope


@scope_api.patch(path="/{scope_identifier}")
async def update_scope_information(
    scope_identifier: typing.Union[str, int],
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administration"]
    ),
    scope_update_data: models.requests.ScopeUpdateData = fastapi.Body(...),
):
    if scope_identifier in ["administration", "account"]:
        raise exceptions.APIException(
            error_code="SCOPE_DEADLOCK",
            error_name="Scope Deadlock Prevented",
            error_description=f"The '{scope_identifier}' scope may not be edited, since this will result in a "
            f"deadlocked system since the authorization service requires this scope",
            status_code=HTTPStatus.FORBIDDEN,
        )
    requested_scope = database.crud.get_scope(scope_identifier)
    if requested_scope is None:
        raise exceptions.APIException(
            error_code="SCOPE_NOT_FOUND",
            error_name="Scope unavailable",
            error_description="The scope you tried to access does not exist in the system",
            status_code=HTTPStatus.NOT_FOUND,
        )
    requested_scope.name = (
        scope_update_data.name if scope_update_data.name is not None else requested_scope.name
    )
    requested_scope.description = (
        scope_update_data.description
        if scope_update_data.name is not None
        else requested_scope.description
    )
    database.crud.store_changed_scope(requested_scope)
    # Get the updated scope data
    return database.crud.get_scope(requested_scope.id)


@scope_api.delete(path="/{scope_identifier}")
async def delete_scope(
    scope_identifier: typing.Union[str, int],
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administration"]
    ),
):
    if scope_identifier in ["administration", "account"]:
        raise exceptions.APIException(
            error_code="SCOPE_DEADLOCK",
            error_name="Scope Deadlock Prevented",
            error_description=f"The requested scope may not be modified or deleted since this will result in locking "
            f"out everyone from the authorization service",
            status_code=HTTPStatus.FORBIDDEN,
        )
    requested_scope = database.crud.get_scope(scope_identifier)
    if requested_scope is None:
        raise exceptions.APIException(
            error_code="SCOPE_NOT_FOUND",
            error_name="Scope unavailable",
            error_description="The scope you tried to access does not exist in the system",
            status_code=HTTPStatus.NOT_FOUND,
        )
    database.crud.delete_scope(requested_scope)
    return fastapi.Response(status_code=HTTPStatus.NO_CONTENT)


@scope_api.put(path="/new")
async def new_scope(
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administration"]
    ),
    new_scope_data: models.requests.ScopeCreationData = fastapi.Body(...),
):
    database.crud.store_new_scope(new_scope_data)
    scope = database.crud.get_scope(new_scope_data.scope_string_value)
    return scope


@scope_api.get(path="/")
async def get_scopes(
    user: models.common.UserAccount = fastapi.Security(
        api.dependencies.get_authorized_user, scopes=["administration"]
    ),
):
    return database.crud.get_scopes()
