"""Module describing the RESTful API Endpoints"""
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestFormStrict
from sqlalchemy.orm import Session
from .dependencies import get_db_session

import data_models
import db.crud.user

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
) -> data_models.Token:
    """Create a access and refresh token for the user to use further on

    :param db_session:
    :param form_data: OAuth2 Password Request data
    :return: Access token and refresh token
    """
    _db_user = db.crud.user.get_user_by_username(db_session, form_data.username)
# ==================
