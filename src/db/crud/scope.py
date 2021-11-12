from sqlalchemy.orm import Session

from db.objects.user import UserScope


def assign_user_to_scope(db: Session, user_id: int, scope_id: int) -> UserScope:
    assignment = UserScope(scope_id=scope_id, user_id=user_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def remove_user_from_scope(db: Session, scope_id: int, user_id: int):
    assignment = UserScope(scope_id=scope_id, user_id=user_id)
    db.refresh(assignment)
    db.delete(assignment)
