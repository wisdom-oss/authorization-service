from sqlalchemy import delete
from sqlalchemy.orm import Session

from data_models import Role
from db.objects import role
from db.objects.user import UserRole


def add_role(db: Session, new_role: Role) -> role.Role:
    db_role = role.Role(role_name=new_role.name, role_description=new_role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def assign_user_to_role(db: Session, user_id: int, role_id: int) -> UserRole:
    assignment = UserRole(user_id=user_id, role_id=role_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment
