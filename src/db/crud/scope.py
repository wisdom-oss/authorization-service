import json
from typing import List, Set

from sqlalchemy.orm import Session
from .role import get_roles_for_user
from db import objects


def assign_user_to_scope(db: Session, user_id: int, scope_id: int) -> objects.UserScope:
    assignment = objects.UserScope(scope_id=scope_id, user_id=user_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def assign_scope_to_token(db: Session, scope_id: int, token_id: int) -> objects.UserScope:
    assignment = objects.TokenScope(scope_id=scope_id, token_id=token_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def assign_named_scope_to_token(db: Session, scope_value: str, token_id: int):
    _scope = db.query(objects.Scope).filter(objects.Scope.scope_value == scope_value).first()
    if _scope is not None:
        assign_scope_to_token(db, _scope.scope_id, token_id)


def get_scope_list_for_user(db: Session, user_id: int) -> Set[str]:
    scope_list = []
    user_scopes = db.query(objects.UserScope).filter(objects.UserScope.user_id == user_id).all()
    for user_scope in user_scopes:
        scope_list.append(user_scope.scope.scope_value)
    user_roles = get_roles_for_user(db, user_id)
    for user_role in user_roles:
        for role_scope in user_role.role.scopes:
            scope_list.append(role_scope.scope.scope_value)
    scope_list.sort(key=str)
    return set(scope_list)


def remove_user_from_scope(db: Session, scope_id: int, user_id: int):
    assignment = objects.UserScope(scope_id=scope_id, user_id=user_id)
    db.refresh(assignment)
    db.delete(assignment)
