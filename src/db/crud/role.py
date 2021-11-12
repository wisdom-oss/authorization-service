from sqlalchemy import delete
from sqlalchemy.orm import Session

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