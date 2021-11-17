from typing import Set

from sqlalchemy.orm import Session

import data_models
from db import objects
from .role import get_roles_for_user


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


def assign_scope_to_refresh_token(db: Session, scope_id: int, token_id: int) -> objects.UserScope:
    assignment = objects.RefreshTokenScopeAssignment(
        scope_id=scope_id,
        refresh_token_id=token_id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def assign_named_scope_to_token(db: Session, scope_value: str, token_id: int):
    _scope = db.query(objects.Scope).filter(objects.Scope.scope_value == scope_value).first()
    if _scope is not None:
        assign_scope_to_token(db, _scope.scope_id, token_id)


def assign_named_scope_to_refresh_token(db: Session, scope_value: str, token_id: int):
    _scope = db.query(objects.Scope).filter(objects.Scope.scope_value == scope_value).first()
    if _scope is not None:
        assign_scope_to_refresh_token(db, _scope.scope_id, token_id)


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


def get_scope_dict_for_user(db: Session, user_id: int) -> dict:
    scope_dict = {}
    user_scopes = db.query(objects.UserScope).filter(objects.UserScope.user_id == user_id).all()
    for assignment in user_scopes:
        scope_dict.update(
            {
                assignment.scope.scope_value: assignment.scope.scope_description
            }
        )
    return scope_dict


def remove_user_from_scope(db: Session, scope_id: int, user_id: int):
    assignment = objects.UserScope(scope_id=scope_id, user_id=user_id)
    db.refresh(assignment)
    db.delete(assignment)


def get_scopes_as_dict(db: Session):
    scope_dict = {}
    scopes = db.query(objects.Scope).all()
    for scope in scopes:
        scope_dict.update(
            {
                scope.scope_value: scope.scope_description
            }
        )
    db.close()
    return scope_dict


def get_user_scopes_as_object_list(db: Session, user_id: int):
    object_list = []
    user_scope_assignments = db.query(objects.UserScope).filter(
        objects.UserScope.user_id ==
        user_id
    ).all()
    for user_scope_assignment in user_scope_assignments:
        object_list.append(data_models.Scope.from_orm(user_scope_assignment.scope))
    return object_list


def get_token_scopes_as_list(db: Session, token_id: int):
    scope_list = []
    for scope in get_token_scopes_as_object_list(db, token_id):
        scope_list.append(scope.scope_value)
    return list(set(scope_list))


def get_token_scopes_as_object_list(db: Session, token_id: int):
    object_list = []
    token_scope_assignments = db.query(objects.TokenScope).filter(
        objects.TokenScope.token_id == token_id
    ).all()
    for token_scope_assignment in token_scope_assignments:
        object_list.append(data_models.Scope.from_orm(token_scope_assignment.scope))
    return object_list


def get_refresh_token_scopes_as_list(db: Session, token_id: int):
    scope_list = []
    for scope in get_refresh_token_scopes_as_object_list(db, token_id):
        scope_list.append(scope.value)
    return list(set(scope_list))


def get_refresh_token_scopes_as_object_list(db: Session, token_id: int):
    object_list = []
    refresh_token_scope_assignments = db.query(objects.RefreshTokenScopeAssignment).filter(
        objects.RefreshTokenScopeAssignment.refresh_token_id == token_id
    ).all()
    for refresh_token_scope_assignment in refresh_token_scope_assignments:
        object_list.append(data_models.Scope.from_orm(refresh_token_scope_assignment.scope))
    return object_list


def get_scope(db: Session, scope_id: int):
    return db.query(objects.Scope).filter(objects.Scope.scope_id == scope_id).first()


def get_scopes(db: Session):
    return db.query(objects.Scope).all()


def add_scope(db: Session, name: str, description: str, value: str):
    _ = objects.Scope(
        scope_name=name,
        scope_description=description,
        scope_value=value
    )
    db.add(_)
    db.commit()
    db.refresh(_)
    return data_models.Scope.from_orm(_)
