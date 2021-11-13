from typing import List

from sqlalchemy import delete
from sqlalchemy.orm import Session

import data_models
from data_models import Role
from db import objects


def add_role(db: Session, new_role: Role) -> objects.Role:
    db_role = objects.Role(role_name=new_role.name, role_description=new_role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
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
        role_dict.update({
            assignment.role.role_id: assignment.role.role_name
        })
    return role_dict
