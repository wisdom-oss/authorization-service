import time
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from db.objects import RefreshToken, Token, UserToken
from db.crud.scope import assign_named_scope_to_token


def add_token(db: Session, user_id: int, scopes=Optional[List[str]]) -> Token:
    _token = Token(
        token=str(uuid.uuid4()),
        expires=time.time() + 3600,
        created=time.time()
    )
    db.add(_token)
    db.commit()
    db.refresh(_token)
    # Assign the token to a user
    _token_assignment = UserToken(
        user_id=user_id,
        token_id=_token.token_id
    )
    db.add(_token_assignment)
    db.commit()
    db.refresh(_token)
    # Create a refresh token
    _refresh_token = RefreshToken(
        refresh_token=str(uuid.uuid4()),
        for_token=_token.token_id,
        expires=time.time() + 604800
    )
    db.add(_refresh_token)
    db.commit()
    if scopes is not None:
        for scope in scopes:
            assign_named_scope_to_token(db, scope, _token.token_id)
    db.refresh(_token)
    return _token


def get_token(db: Session, token_id: int):
    pass


def get_access_token_via_value(db: Session, token_value: str):
    return db.query(Token).filter(Token.token == token_value).first()
