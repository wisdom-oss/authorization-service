"""Module describing the RESTful API Endpoints"""
import time
import uuid
from typing import Optional

from fastapi import Depends, FastAPI, Form, Security, Request
from fastapi.responses import UJSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestFormStrict, SecurityScopes
from sqlalchemy.orm import Session
from starlette import status
from passlib.hash import pbkdf2_sha512

from db import DatabaseSession, engine
from db.crud.scope import get_scope_list_for_user, get_scopes_as_dict, \
    get_token_scopes_as_list, get_token_scopes_as_object_list, get_user_scopes_as_object_list
from db.crud.token import add_token, get_access_token_via_value, get_refresh_token_via_value
from db.crud.user import get_user_by_username
from .dependencies import get_db_session

import data_models
import db.crud.user
from .exceptions import AuthorizationException

# Initialize all database connections
db.TableBase.metadata.create_all(bind=engine)
auth_service = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='oauth/token',
    scheme_name='WISdoM Authorization',
    scopes=get_scopes_as_dict(DatabaseSession()),
    auto_error=False
)


async def get_user(
        security_scopes: SecurityScopes,
        token: str = Depends(oauth2_scheme),
        db_session=Depends(get_db_session)
):
    if token is None or token == "undefined":
        raise AuthorizationException("invalid_request")
    token_data = get_access_token_via_value(db_session, token)
    user_data = get_user_by_username(db_session, token_data.user[0].user.username)
    token_scopes = get_token_scopes_as_list(db_session, token_data.token_id)
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise AuthorizationException(
                "insufficient_scope",
                needed_scope=security_scopes.scope_str
            )
    return data_models.User(
        id=user_data.user_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username
    )


# ===== EXCEPTION HANDLERS =====
@auth_service.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    if exc.error_code == 'invalid_request':
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": exc.error_code
            },
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )
    if exc.error_code == 'invalid_token':
        return UJSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": exc.error_code
            },
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )
    if exc.error_code == 'insufficient_scope':
        return UJSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": exc.error_code
            },
            headers={
                "WWW-Authenticate": f"Bearer scope={exc.needed_scope}"
            }
        )


# ===== ROUTES =====
@auth_service.post(
    path='/oauth/token'
)
async def login(
        form_data: OAuth2PasswordRequestFormStrict = Depends(),
        db_session: Session = Depends(get_db_session)
):
    """Create a access and refresh token for the user to use further on

    :param db_session:
    :param form_data: OAuth2 Password Request data
    :return: Access token and refresh token
    """
    _db_user = db.crud.user.get_user_by_username(db_session, form_data.username)
    if _db_user is None:
        return UJSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error":             "invalid_grant",
                "error_description": "The supplied credentials are not valid"
            }
        )
    # Check if the password matches the one saved in the database
    if not pbkdf2_sha512.verify(form_data.password, _db_user.password):
        return UJSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error":             "invalid_grant",
                "error_description": "The supplied credentials are not valid"
            }
        )
    # Check if the user is set to active
    if not _db_user.is_active:
        return UJSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error":             "invalid_grant",
                "error_description": "The user account is not authorized to receive a token"
            }
        )
    # Check if the request included scopes if yes check if those are valid
    _user_scopes = get_scope_list_for_user(db_session, _db_user.user_id)
    if len(form_data.scopes) == 0:
        scopes = ""
        for scope in _user_scopes:
            scopes += f'{scope} '
        scopes = scopes.strip()
        _generated_token = add_token(db_session, _db_user.user_id, _user_scopes)
        _token = data_models.Token(
            access_token=_generated_token.token,
            refresh_token=_generated_token.refresh_token[0].refresh_token,
            scope=scopes
        )
        return _token
    else:
        for scope in form_data.scopes:
            if scope not in _user_scopes:
                return UJSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error":             "invalid_scope",
                        "error_description": "The user account is not authorized to use one of "
                                             "the requested scopes. Please check your users scope"
                    }
                )
        _generated_token = add_token(db_session, _db_user.user_id, form_data.scopes)
        scopes = ""
        for scope in form_data.scopes:
            scopes += f'{scope} '
        scopes = scopes.strip()
        _token = data_models.Token(
            access_token=_generated_token.token,
            refresh_token=_generated_token.refresh_token[0].refresh_token,
            scope=scopes
        )
        return _token


@auth_service.post(
    path='/oauth/check_token'
)
async def check_token(
        db_session: Session = Depends(get_db_session),
        user: data_models.User = Security(get_user),
        token: str = Form(...)
):
    # Check the access_token table for a token with the value
    _token = get_access_token_via_value(db_session, token)
    if _token is not None:
        if time.time() <= _token.expires:
            # Create string of the scopes available for this user
            scopes = " "
            for token_scope in _token.scopes:
                scopes += f'{token_scope.scope.scope_value} '
            scopes = scopes.strip()
            return data_models.IntrospectionResponse(
                active=True,
                scope=scopes,
                username=_token.user[0].user.username,
                token_type='access_token',
                exp=_token.expires,
                iat=_token.created
            ).dict(exclude_unset=True, exclude_none=True)
        else:
            return data_models.IntrospectionResponse(
                active=False
            ).dict(exclude_unset=True, exclude_none=True)
    _token = get_refresh_token_via_value(db_session, token)
    if _token is not None:
        if time.time() <= _token.expires:
            # Create string of the scopes available for this token
            return data_models.IntrospectionResponse(
                active=True,
                token_type='refresh_token',
                username=_token.access_token.user[0].user.username,
                exp=_token.expires,
            ).dict(exclude_unset=True, exclude_none=True)
    return data_models.IntrospectionResponse(
        active=False
    ).dict(exclude_unset=True, exclude_none=True)