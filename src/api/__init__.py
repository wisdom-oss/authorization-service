"""Module describing the RESTful API Endpoints"""
import time

from fastapi import Depends, FastAPI, Form, Request, Security
from fastapi.responses import UJSONResponse
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from passlib.hash import pbkdf2_sha512
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

import data_models
import db.crud.user
from db import DatabaseSession, engine
from db.crud.role import get_roles_for_user_as_object_list
from db.crud.scope import (get_refresh_token_scopes_as_list, get_scope_list_for_user,
                           get_scopes_as_dict, get_token_scopes_as_list,
                           get_token_scopes_as_object_list)
from db.crud.token import add_refreshed_token, add_token, get_access_token_via_value, \
    get_refresh_token_via_value
from db.crud.user import get_user_by_username
from .dependencies import CustomizedOAuth2PasswordRequestForm, get_db_session
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
        raise AuthorizationException("invalid_request", status.HTTP_400_BAD_REQUEST)
    token_data = get_access_token_via_value(db_session, token)
    if token_data is None:
        raise AuthorizationException('invalid_token', status.HTTP_401_UNAUTHORIZED)
    if not token_data.active:
        raise AuthorizationException('invalid_token', status.HTTP_401_UNAUTHORIZED)
    if time.time() >= token_data.expires:
        raise AuthorizationException('invalid_token', status.HTTP_401_UNAUTHORIZED)
    user_data = get_user_by_username(db_session, token_data.user[0].user.username)
    token_scopes = get_token_scopes_as_list(db_session, token_data.token_id)
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise AuthorizationException(
                "insufficient_scope",
                status.HTTP_401_UNAUTHORIZED,
                optional_data=f"scope={security_scopes.scope_str}"
            )
    return data_models.User(
        id=user_data.user_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        scopes=get_token_scopes_as_object_list(db_session, token_data.token_id),
        roles=get_roles_for_user_as_object_list(db_session, user_data.user_id)
    )


# ===== EXCEPTION HANDLERS =====
@auth_service.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    return UJSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code
        },
        headers={
            'WWW-Authenticate': f'Bearer {exc.optional_data}'.strip()
        }
    )


# ===== ROUTES =====
@auth_service.post(
    path='/oauth/token'
)
async def login(
        form_data: CustomizedOAuth2PasswordRequestForm = Depends(),
        db_session: Session = Depends(get_db_session)
):
    if form_data.grant_type == 'refresh_token':
        if form_data.refresh_token == "" or form_data.refresh_token.strip() == "":
            raise AuthorizationException('invalid_request', status.HTTP_400_BAD_REQUEST)
        refresh_token_data = get_refresh_token_via_value(db_session, form_data.refresh_token)
        if refresh_token_data is None \
                or refresh_token_data.active is False \
                or time.time() >= refresh_token_data.expires:
            raise AuthorizationException('invalid_grant', status.HTTP_400_BAD_REQUEST)
        if len(form_data.scopes) == 0:
            scopes = get_refresh_token_scopes_as_list(
                db_session, refresh_token_data.refresh_token_id
            )
            token = add_refreshed_token(db_session, form_data.refresh_token, scopes=scopes)
            _token = data_models.Token(
                access_token=token.token,
                refresh_token=token.refresh_token_assignments[0].refresh_token.refresh_token,
                scope=" ".join(scopes)
            )
            return _token

        else:
            for scope in form_data.scopes:
                for scope_assignment in refresh_token_data.scope_assignments:
                    if scope_assignment.scope.scope_value != scope:
                        raise AuthorizationException('invalid_scope', status.HTTP_400_BAD_REQUEST)
            scopes = get_refresh_token_scopes_as_list(
                db_session, refresh_token_data.refresh_token_id
            )
            token = add_refreshed_token(db_session, form_data.refresh_token, scopes=scopes)
            _token = data_models.Token(
                access_token=token.token,
                refresh_token=token.refresh_token_assignments[0].refresh_token.refresh_token,
                scope=" ".join(scopes)
            )
            return _token
    if form_data.grant_type == 'password':
        _db_user = db.crud.user.get_user_by_username(db_session, form_data.username)
        if _db_user is None:
            raise AuthorizationException('invalid_grant', status.HTTP_400_BAD_REQUEST)
        # Check if the password matches the one saved in the database
        if not pbkdf2_sha512.verify(form_data.password, _db_user.password):
            raise AuthorizationException('invalid_grant', status.HTTP_400_BAD_REQUEST)
        # Check if the user is set to active
        if not _db_user.is_active:
            raise AuthorizationException('invalid_grant', status.HTTP_400_BAD_REQUEST)
        # Check if the request included scopes if yes check if those are valid
        _user_scopes = get_scope_list_for_user(db_session, _db_user.user_id)
        if len(form_data.scopes) == 0:
            scopes = " ".join(_user_scopes)
            token = add_token(db_session, _db_user.user_id, _user_scopes)
            _token = data_models.Token(
                access_token=token.token,
                refresh_token=token.refresh_token_assignments[0].refresh_token.refresh_token,
                scope=scopes
            )
            return _token
        else:
            for scope in form_data.scopes:
                if scope not in _user_scopes:
                    raise AuthorizationException(
                        'invalid_scope',
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            token = add_token(db_session, _db_user.user_id, form_data.scopes)
            scopes = " ".join(form_data.scopes)
            _token = data_models.Token(
                access_token=token.token,
                refresh_token=token.refresh_token_assignments[0].refresh_token.refresh_token,
                scope=scopes
            )
            return _token
    raise AuthorizationException('unsupported_grant_type', status.HTTP_400_BAD_REQUEST)


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


@auth_service.post(
    path='/oauth/revoke'
)
async def revoke_token(
        user: data_models.User = Security(get_user, scopes=["me"]),
        db_session: Session = Depends(get_db_session),
        token: str = Form(...)
):
    # Get information about the token, starting with the refresh_tokens
    token_info = get_refresh_token_via_value(db_session, token)
    # Check if the token is owned by the current user
    if token_info.access_token_assignment[0].access_token.user[0].user_id == user.id:
        if token_info is not None:
            for assignment in token_info.access_token_assignment:
                assignment.access_token.active = False
                assignment.refresh_token.active = False
                db_session.commit()
            return Response(status_code=200, content="refresh")
        token_info = get_access_token_via_value(db_session, token)
        if token_info is not None:
            for assignment in token_info.refresh_token_assignments:
                assignment.refresh_token.active = False
                assignment.access_token.active = False
                db_session.commit()
            token_info.active = False
            db_session.commit()
            return Response(status_code=200, content="access")
    else:
        if "admin" not in user.scopes:
            raise AuthorizationException(
                'insufficient_scope', status.HTTP_403_FORBIDDEN, optional_data="scope=admin"
            )
        if token_info is not None:
            for assignment in token_info.access_token_assignment:
                assignment.access_token.active = False
                assignment.refresh_token.active = False
                db_session.commit()
            return Response(status_code=200)
        token_info = get_access_token_via_value(db_session, token)
        if token_info is not None:
            for assignment in token_info.refresh_token_assignments:
                assignment.refresh_token.active = False
                assignment.access_token.active = False
                db_session.commit()
            token_info.active = False
            db_session.commit()
            return Response(status_code=200)
    return Response(status_code=status.HTTP_200_OK)

