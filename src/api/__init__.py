"""Module describing the RESTful API Endpoints"""
import time
from typing import List

import sqlalchemy.exc
from fastapi import Body, Depends, FastAPI, Form, Request, Security
from fastapi.exceptions import RequestValidationError
from fastapi.responses import UJSONResponse
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from passlib.hash import pbkdf2_sha512
from pydantic import constr, parse_obj_as
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import Response

import data_models
import db.crud.user
from db import DatabaseSession, engine
from db.crud.role import (add_role, get_role_dict_for_user, get_role_information, get_roles,
                          get_roles_for_user_as_list,
                          get_roles_for_user_as_object_list, update_role)
from db.crud.scope import (add_scope, get_refresh_token_scopes_as_list, get_scope,
                           get_scope_dict_for_user,
                           get_scope_list_for_user, get_scopes, get_scopes_as_dict,
                           get_scopes_for_role, get_token_scopes_as_list,
                           get_token_scopes_as_object_list, update_scope)
from db.crud.token import (add_refreshed_token, add_token, get_access_token_via_value,
                           get_refresh_token_via_value)
from db.crud.user import add_user, get_user_by_id, get_user_by_username, get_users, remove_user, \
    update_user
from .dependencies import CustomizedOAuth2PasswordRequestForm, get_db_session
from .exceptions import AuthorizationException, ObjectNotFoundException

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
        raise AuthorizationException(
            "invalid_request", status.HTTP_400_BAD_REQUEST,
            error_description="There is no Bearer Token present in the request."
        )
    token_data = get_access_token_via_value(db_session, token)
    if token_data is None:
        raise AuthorizationException('invalid_token', status.HTTP_401_UNAUTHORIZED)
    if not token_data.active:
        raise AuthorizationException('invalid_token', status.HTTP_401_UNAUTHORIZED)
    if time.time() >= token_data.expires:
        raise AuthorizationException('invalid_token', status.HTTP_401_UNAUTHORIZED)
    user_data = get_user_by_username(db_session, token_data.user[0].user.username)
    if not user_data.is_active:
        raise AuthorizationException('invalid_token', status.HTTP_401_UNAUTHORIZED)
    token_scopes = get_token_scopes_as_list(db_session, token_data.token_id)
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise AuthorizationException(
                "insufficient_scope",
                status.HTTP_401_UNAUTHORIZED,
                optional_data=f"scope={security_scopes.scope_str}"
            )
    _user = data_models.BaseUser.from_orm(user_data)
    _user.scopes = get_token_scopes_as_object_list(db_session, token_data.token_id)
    _user.roles = get_roles_for_user_as_object_list(db_session, user_data.user_id)
    return _user


# ===== EXCEPTION HANDLERS =====
@auth_service.exception_handler(AuthorizationException)
async def authorization_exception_handler(_request: Request, exc: AuthorizationException):
    if exc.error_description is None:
        return UJSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code
            },
            headers={
                'WWW-Authenticate': f'Bearer {exc.optional_data}'.strip()
            }
        )
    else:
        return UJSONResponse(
            status_code=exc.status_code,
            content={
                "error":             exc.error_code,
                "error_description": exc.error_description
            },
            headers={
                'WWW-Authenticate': f'Bearer {exc.optional_data}'.strip()
            }
        )


@auth_service.exception_handler(ObjectNotFoundException)
async def object_not_found_exception_handler(_request: Request, _exc: ObjectNotFoundException):
    return Response(
        status_code=status.HTTP_404_NOT_FOUND
    )


@auth_service.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_request: Request, exc: RequestValidationError):
    return UJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "errors": exc.errors()
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
            return _token.dict(by_alias=False)
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
        user: data_models.BaseUser = Security(get_user),
        token: str = Form(...),
        scope: str = Form(None)
):
    # Check the access_token table for a token with the value
    _token = get_access_token_via_value(db_session, token)
    if _token is not None:
        if time.time() <= _token.expires:
            # Create string of the scopes available for this user
            available_scopes = []
            for token_scope in _token.scopes:
                available_scopes.append(token_scope.scope.scope_value)
            if scope is not None:
                for _ in scope.split(" "):
                    if _ not in available_scopes:
                        return data_models.IntrospectionResponse(
                            active=False
                        ).dict(exclude_unset=True, exclude_none=True)
                return data_models.IntrospectionResponse(
                    active=True,
                    scope=scope,
                    username=_token.user[0].user.username,
                    token_type='access_token',
                    exp=_token.expires,
                    iat=_token.created
                ).dict(exclude_unset=True, exclude_none=True)
            else:
                return data_models.IntrospectionResponse(
                    active=True,
                    scope=" ".join(available_scopes),
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
                iat=None
            ).dict(exclude_unset=True, exclude_none=True)
    return data_models.IntrospectionResponse(
        active=False
    ).dict(exclude_unset=True, exclude_none=True)


@auth_service.post(
    path='/oauth/revoke'
)
async def revoke_token(
        user: data_models.BaseUser = Security(get_user, scopes=["me"]),
        db_session: Session = Depends(get_db_session),
        token: str = Form(...)
):
    # Get information about the token, starting with the refresh_tokens
    token_info = get_refresh_token_via_value(db_session, token)
    # Check if the token is owned by the current user
    if token_info.access_token_assignment[0].access_token.user[0].user_id == user.user_id:
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


@auth_service.get(
    path='/users/me'
)
def get_user_information(
        user: data_models.BaseUser = Security(get_user, scopes=["me"]),
        db_session: Session = Depends(get_db_session)
):
    _user = user
    _user.scopes = get_scope_dict_for_user(db_session, user.user_id)
    _user.roles = get_role_dict_for_user(db_session, user.user_id)
    return _user


@auth_service.patch(
    path='/users/me'
)
def update_current_user(
        user: data_models.BaseUser = Security(get_user, scopes=["me"]),
        db_session: Session = Depends(get_db_session),
        password: str = Body(..., embed=True)
):
    _user = update_user(db_session, user.user_id, password=password)
    if pbkdf2_sha512.verify(password, _user.password):
        updated_user = data_models.BaseUser.from_orm(_user)
        updated_user.roles = get_role_dict_for_user(db_session, updated_user.user_id)
        updated_user.scopes = get_scope_dict_for_user(db_session, updated_user.user_id)
        return updated_user
    else:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@auth_service.get(
    path='/users/{user_id}'
)
async def get_user_information(
        user_id: int, _current_user=Security(get_user, scopes=["admin"]), db_session: Session =
        Depends(get_db_session)
):
    user_data = get_user_by_id(db_session, user_id)
    if user_data is None:
        return UJSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "no_such_user"
            }
        )
    _user = data_models.BaseUser.from_orm(user_data)
    _user.roles = get_role_dict_for_user(db_session, user_data.user_id)
    _user.scopes = get_scope_dict_for_user(db_session, user_data.user_id)
    return _user


@auth_service.delete(
    path='/users/{user_id}',
)
async def delete_user(
        user_id: int,
        _current_user=Security(get_user, scopes=["admin"]),
        db_session: Session = Depends(get_db_session)
):
    remove_user(db_session, user_id)
    return Response(status_code=status.HTTP_200_OK)


@auth_service.get(
    path='/users'
)
async def get_all_users(
       _current_user=Security(get_user, scopes=["admin"]),
        db_session: Session = Depends(get_db_session)
):
    users = get_users(db_session)
    user_list = parse_obj_as(List[data_models.BaseUser], users)
    for user in user_list:
        user.scopes = get_scope_dict_for_user(db_session, user.user_id)
        user.roles = get_role_dict_for_user(db_session, user.user_id)
    return user_list


@auth_service.put(
    path='/users'
)
async def add_user_to_system(
       _current_user=Security(get_user, scopes=["admin"]),
        db_session: Session = Depends(get_db_session),
        new_user: data_models.NewUser = Body(...)
):
    try:
        user = add_user(db_session, new_user)
        _user = data_models.BaseUser.from_orm(user)
        _user.scopes = get_scope_dict_for_user(db_session, user.user_id)
        _user.roles = get_role_dict_for_user(db_session, user.user_id)
        return _user
    except sqlalchemy.exc.IntegrityError as error:
        print(error)
        return UJSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "User already exists",
            }
        )


@auth_service.patch(
    path='/users'
)
async def update_user_information(
        _current_user=Security(get_user, scopes=["admin"]),
        db_session: Session = Depends(get_db_session),
        new_user_information: data_models.UserUpdate = Body(...)
):
    _user = update_user(db_session, **new_user_information.dict(exclude_none=True))
    updated_user = data_models.BaseUser.from_orm(_user)
    updated_user.roles = get_role_dict_for_user(db_session, updated_user.user_id)
    updated_user.scopes = get_scope_dict_for_user(db_session, updated_user.user_id)
    return updated_user


@auth_service.get(
    path='/scopes/{scope_id}'
)
async def get_scope_information(
        scope_id: int,
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"])
):
    scope_information = get_scope(db_session, scope_id)
    return data_models.Scope.from_orm(scope_information)


@auth_service.delete(
    path='/scopes/{scope_id}'
)
async def delete_scope(
        scope_id: int,
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"])
):
    scope = get_scope(db_session, scope_id)
    if scope is not None:
        db_session.delete(scope)
        db_session.commit()
    return Response(status_code=status.HTTP_200_OK)


@auth_service.get(
    path='/scopes'
)
async def get_all_scopes(
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"])
):
    all_scopes = get_scopes(db_session)
    scopes = parse_obj_as(List[data_models.Scope], all_scopes)
    return scopes


@auth_service.put(
    path='/scopes'
)
async def add_scope_to_system(
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"]),
        name: constr(max_length=200, strip_whitespace=True) = Body(...),
        description: constr(strip_whitespace=True) = Body(...),
        value: constr(strip_whitespace=True, max_length=150) = Body(...)
):
    try:
        return add_scope(db_session, name, description, value)
    except sqlalchemy.exc.IntegrityError as error:
        print(error)
        return UJSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Scope already exists",
            }
        )


@auth_service.patch(
    path='/scopes'
)
async def update_scopes(
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"]),
        scope_data: data_models.Scope = Body(...)
):
    return update_scope(db_session, **scope_data.dict())


@auth_service.get(
    path='/roles/{role_id}'
)
async def get_role(
        role_id: int,
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"])
):
    _ = get_role_information(db_session, role_id)
    if _ is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    role = data_models.Role.from_orm(_)
    role.role_scopes = get_scopes_for_role(db_session, role.role_id)
    return role


@auth_service.delete(
    path='/roles/{role_id}'
)
async def delete_role(
        role_id: int,
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"])
):
    role = get_role_information(db_session, role_id)
    if role is not None:
        db_session.delete(role)
        db_session.commit()
    return Response(status_code=status.HTTP_200_OK)


@auth_service.get(
    path='/roles'
)
async def get_all_roles(
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"])
):
    _ = get_roles(db_session)
    roles = parse_obj_as(List[data_models.Role], _)
    for role in roles:
        role.role_scopes = get_scopes_for_role(db_session, role.role_id)
    return roles


@auth_service.put(
    path='/roles'
)
async def add_role_to_system(
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"]),
        name: constr(max_length=200, strip_whitespace=True) = Body(...),
        description: constr(strip_whitespace=True) = Body(...),
        scopes: str = Body("")
):
    try:
        return data_models.Role.from_orm(add_role(db_session, name, description, scopes.split(" ")))
    except sqlalchemy.exc.IntegrityError as error:
        print(error)
        return UJSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Role already exists",
            }
        )


@auth_service.patch(
    path='/roles'
)
async def add_role_to_system(
        db_session: Session = Depends(get_db_session),
        _current_user: data_models.BaseUser = Security(get_user, scopes=["admin"]),
        role: data_models.Role = Body(...)
):
    updated_role = data_models.Role.from_orm(update_role(db_session, **role.dict()))
    updated_role.role_scopes = get_scopes_for_role(db_session, updated_role.role_id)
    return updated_role
