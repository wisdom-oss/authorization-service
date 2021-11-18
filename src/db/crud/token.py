import time
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from db.objects import RefreshToken, RefreshTokenAssignment, Token, UserToken
from db.crud.scope import assign_named_scope_to_token, assign_named_scope_to_refresh_token


def add_token(
        db: Session, user_id: int, scopes=Optional[List[str]],
        refresh_token=RefreshToken(
            refresh_token=str(uuid.uuid4()),
            expires=time.time() + 604800,
            active=True
        )
) -> Token:
    _token = Token(
        token=str(uuid.uuid4()),
        expires=time.time() + 3600,
        created=time.time(),
        active=True
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
    _refresh_token = refresh_token
    db.add(_refresh_token)
    db.commit()
    _refresh_token_assignment = RefreshTokenAssignment(
        refresh_token_id=_refresh_token.refresh_token_id,
        access_token_id=_token.token_id
    )
    db.add(_refresh_token_assignment)
    db.commit()
    if scopes is not None:
        for scope in scopes:
            assign_named_scope_to_token(db, scope, _token.token_id)
            assign_named_scope_to_refresh_token(db, scope, _refresh_token.refresh_token_id)
    db.refresh(_token)
    return _token


def add_refreshed_token(
        db: Session,
        refresh_token: str,
        scopes=Optional[List[str]]
) -> Token:
    _data = get_refresh_token_via_value(db, refresh_token)
    return add_token(
        db, _data.access_token_assignment[0].access_token.user[0].user_id, scopes, _data
    )


def get_access_token_via_value(db: Session, token_value: str) -> Token:
    return db.query(Token).filter(Token.token == token_value).first()


def get_refresh_token_via_value(db: Session, token_value: str) -> RefreshToken:
    return db.query(RefreshToken).filter(RefreshToken.refresh_token == token_value).first()
