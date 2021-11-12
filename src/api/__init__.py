"""Module describing the RESTful API Endpoints"""
import uuid

from fastapi import Depends, FastAPI
from fastapi.responses import UJSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestFormStrict
from sqlalchemy.orm import Session
from starlette import status
from passlib.hash import bcrypt_sha256

from db import engine
from db.crud.scope import get_scopes_for_user
from db.crud.token import add_token
from .dependencies import get_db_session

import data_models
import db.crud.user

db.TableBase.metadata.create_all(bind=engine)

auth_service = FastAPI(
    docs_url=None,
    redoc_url=None
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='oauth/token',
    scheme_name='WISdoM Authorization'
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
    if not bcrypt_sha256.verify(form_data.password, _db_user.password):
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
    _user_scopes = get_scopes_for_user(db_session, _db_user.user_id)
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
