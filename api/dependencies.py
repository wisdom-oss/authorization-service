"""Package containing some custom dependencies for the API application"""
import datetime
import http

import fastapi.security
import pytz.reference
from pydantic import SecretStr

import database.crud
import exceptions
import models.common

__oauth2_scheme = fastapi.security.OAuth2PasswordBearer(
    tokenUrl="oauth/token", scheme_name="WISdoM Central Authorization", auto_error=False
)


def get_authorized_user(
    scopes: fastapi.security.SecurityScopes,
    access_token: str = fastapi.Depends(__oauth2_scheme),
) -> models.common.UserAccount:
    """
    Get the user whose authorization information is present in the headers

    :param scopes: The scopes that are needed for accessing the endpoint
    :type scopes: fastapi.security.SecurityScopes
    :param access_token: The access token used to access the endpoint
    :type access_token: str
    :return: The user whose authorization information was used to access the service
    :rtype: models.common.UserAccount
    """
    # Check if any token has been set
    if access_token in (None, "undefined"):
        raise exceptions.APIException(
            error_code="INVALID_REQUEST",
            error_name="Invalid Request",
            error_description="The request did not contain the necessary credentials to allow processing this request",
            status_code=http.HTTPStatus.BAD_REQUEST,
        )
    # Now get some data about the access token
    token_information = database.crud.get_access_token_data(access_token)
    if token_information is None:
        raise exceptions.APIException(
            error_code="INVALID_TOKEN",
            error_name="Invalid Bearer Token",
            error_description="The request did not contain the correct credentials to allow processing this request",
            status_code=http.HTTPStatus.UNAUTHORIZED,
        )
    if datetime.datetime.now(tz=pytz.reference.LocalTimezone()) > token_information.expires:
        raise exceptions.APIException(
            error_code="EXPIRED_TOKEN",
            error_name="Expired Bearer Token",
            error_description="The request did not contain a alive Bearer token",
            status_code=http.HTTPStatus.UNAUTHORIZED,
        )
    if datetime.datetime.now(tz=pytz.reference.LocalTimezone()) < token_information.created:
        raise exceptions.APIException(
            error_code="TOKEN_BEFORE_CREATION",
            error_name="Credentials used too early",
            error_description="The credentials used for this request are currently not valid",
            status_code=http.HTTPStatus.UNAUTHORIZED,
        )
    # Get the information about the user account
    user = database.crud.get_user_account(token_information.owner_id)
    if user is None:
        raise exceptions.APIException(
            error_code="USER_DELETED",
            error_name="User deleted",
            error_description="The account used to access this resource was deleted",
            status_code=http.HTTPStatus.UNAUTHORIZED,
        )
    if not user.active:
        raise exceptions.APIException(
            error_code="USER_DISABLED",
            error_name="User Disabled",
            error_description="The account used to access this resource is currently disabled",
            status_code=http.HTTPStatus.FORBIDDEN,
        )
    # Now get the users scopes
    access_token_scopes = database.crud.get_access_token_scopes(token_information)
    required_scopes = set(sorted(scopes.scopes))
    available_scopes = set(sorted([scope.scope_string_value for scope in access_token_scopes]))
    if not required_scopes.issubset(available_scopes):
        raise exceptions.APIException(
            error_code="MISSING_PRIVILEGES",
            error_name="Missing Privileges",
            error_description="The account used to access this resource does not have the privileges to access this "
            "endpoint",
            status_code=http.HTTPStatus.FORBIDDEN,
        )
    return user


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
        grant_type: str = fastapi.Form(None, regex="(?:^password$|^refresh_token$)"),
        username: str = fastapi.Form(None, min_length=1),
        password: SecretStr = fastapi.Form(None, min_length=1),
        refresh_token: str = fastapi.Form(None, min_length=1),
        scope: str = fastapi.Form(""),
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
        if self.grant_type == "password":
            # Check if the username and password are present in the request
            if None in (username, password) or refresh_token is not None:
                raise exceptions.APIException(
                    error_code="INVALID_ARGUMENTS_FOR_GRANT_TYPE",
                    error_name="Invalid Arguments for specified grant type",
                    error_description="The form did not contain the necessary arguments for the specified grant type "
                    "or arguments from other grant types have been sent",
                    status_code=http.HTTPStatus.BAD_REQUEST,
                )
            # Save the username and password after passing this check
            self.username = username.strip()
            self.password = password
        if self.grant_type == "refresh_token":
            if refresh_token is None or None not in (username, password):
                raise exceptions.APIException(
                    error_code="INVALID_ARGUMENTS_FOR_GRANT_TYPE",
                    error_name="Invalid Arguments for specified grant type",
                    error_description="The form did not contain the necessary arguments for the specified grant type "
                    "or arguments from other grant types have been sent",
                    status_code=http.HTTPStatus.BAD_REQUEST,
                )
            # Save the refresh token after passing this check
            self.refresh_token = refresh_token.strip()
        # Save the scopes to the form
        self.scopes = scope.strip()
