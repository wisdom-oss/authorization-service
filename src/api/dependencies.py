"""Module for extra dependencies like own request bodies or database connections"""
from typing import Optional

from fastapi import Form
from starlette import status

from .exceptions import AuthorizationException
from db import DatabaseSession


def get_db_session() -> DatabaseSession:
    """Get a opened Database session which can be used to manipulate orm data

    :return: Database Session
    :rtype: DatabaseSession
    """
    db = DatabaseSession()
    try:
        yield db
    finally:
        db.close()


class CustomizedOAuth2PasswordRequestForm:
    """
    This is a dependency class, use it like:

        @app.post("/login")
        def login(form_data: OAuth2PasswordRequestForm = Depends()):
            data = form_data.parse()
            print(data.username)
            print(data.password)
            for scope in data.scopes:
                print(scope)
            if data.client_id:
                print(data.client_id)
            if data.client_secret:
                print(data.client_secret)
            return data


    It creates the following Form request parameters in your endpoint:

    grant_type: the OAuth2 spec says it is required and MUST be the fixed string "password".
        Nevertheless, this dependency class is permissive and allows not passing it. If you want
        to enforce it,
        use instead the OAuth2PasswordRequestFormStrict dependency.
    username: username string. The OAuth2 spec requires the exact field name "username".
    password: password string. The OAuth2 spec requires the exact field name "password".
    scope: Optional string. Several scopes (each one a string) separated by spaces. E.g.
        "items:read items:write users:read profile openid"
    client_id: optional string. OAuth2 recommends sending the client_id and client_secret (if any)
        using HTTP Basic auth, as: client_id:client_secret
    client_secret: optional string. OAuth2 recommends sending the client_id and client_secret (if
    any)
        using HTTP Basic auth, as: client_id:client_secret
    """

    def __init__(
            self,
            grant_type: str = Form(None, regex="(?:^password$|^refresh_token$)"),
            username: str = Form(None),
            password: str = Form(None),
            scope: str = Form(""),
            refresh_token: str = Form(None),
            client_id: Optional[str] = Form(None),
            client_secret: Optional[str] = Form(None),
    ):
        self.grant_type = grant_type
        if self.grant_type == 'password':
            self.username = username
            self.password = password
            if self.username is None or self.password is None or refresh_token is not None:
                raise AuthorizationException('invalid_request', status.HTTP_400_BAD_REQUEST)
        if self.grant_type == 'refresh_token':
            self.refresh_token = refresh_token
            if self.refresh_token is None or username is not None or password is not None:
                raise AuthorizationException('invalid_request', status.HTTP_400_BAD_REQUEST)

        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret
