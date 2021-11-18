from typing import List

from sqlalchemy import delete
from sqlalchemy.orm import Session

import data_models
from data_models import Role
from db import objects


def add_role(db: Session, name: str, description: str, scopes: List[str]) -> objects.Role:
    db_role = objects.Role(role_name=name, role_description=description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    for scope_value in scopes:
        assign_scope_to_role(db, db_role.role_id, scope_value)
    return db_role


def assign_user_to_role(db: Session, user_id: int, role_id: int) -> objects.UserRole:
    assignment = objects.UserRole(user_id=user_id, role_id=role_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def get_roles_for_user(db: Session, user_id: int):
    return db.query(objects.UserRole).filter(objects.UserRole.user_id == user_id).all()


def get_roles_for_user_as_object_list(db: Session, user_id: int) -> List[data_models.Role]:
    object_list = []
    assignments = get_roles_for_user(db, user_id)
    for role_assignment in assignments:
        object_list.append(data_models.Role.from_orm(role_assignment.role))
    return object_list


def get_roles_for_user_as_list(db: Session, user_id: int) -> List[str]:
    role_list = []
    assignments = get_roles_for_user(db, user_id)
    for role_assignment in assignments:
        role_list.append(role_assignment.role.role_name)
    return role_list


def get_role_dict_for_user(db: Session, user_id: int) -> dict:
    role_dict = {}
    assignments = get_roles_for_user(db, user_id)
    for assignment in assignments:
        role_dict.update(
            {
                assignment.role.role_id: assignment.role.role_name
            }
        )
    return role_dict


def get_roles(db: Session):
    return db.query(objects.Role).all()


def get_role_information(db: Session, role_id: int):
    return db.query(objects.Role).filter(objects.Role.role_id == role_id).first()


def assign_scope_to_role(db: Session, role_id: int, scope_value: str):
    scope = db.query(objects.Scope).filter(objects.Scope.scope_value == scope_value).first()
    if scope is None:
        return None
    scope_assoc = objects.RoleScope(
        role_id=role_id,
        scope_id=scope.scope_id
    )
    db.add(scope_assoc)
    db.commit()
    db.refresh(scope_assoc)
    return scope_assoc


def update_role(db: Session, role_id: int, **new):
    role = get_role_information(db, role_id)
    if "role_name" in new and new["role_name"] is not None:
        role.role_name = new["role_name"].strip()
    if "role_description" in new and new["role_description"] is not None:
        role.role_description = new["role_description"].strip()
    if "role_scopes" in new and new["role_scopes"] is not None:
        print(new["role_scopes"])
        scopes = new["role_scopes"].strip().split(" ")
        db.query(objects.RoleScope).filter(objects.RoleScope.role_id == role_id).delete()
        for scope in scopes:
            assign_scope_to_role(db, role_id, scope)
    db.commit()
    db.refresh(role)
    return role
