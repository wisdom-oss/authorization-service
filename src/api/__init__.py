"""Module describing the RESTful API Endpoints"""
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer

auth_service = FastAPI(
    docs_url=None,
    redoc_url=None
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='oauth/token',
    scheme_name='WISdoM Authorization'
)