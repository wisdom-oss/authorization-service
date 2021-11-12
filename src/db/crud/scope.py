from sqlalchemy.orm import Session

from db.objects.user import UserScope


def assign_user_to_scope(db: Session, user_id: int, scope_id: int) -> UserScope:
    _db_assignment = db.query(UserScope).filter(
        UserScope.user_id == user_id,
        UserScope.scope_id == scope_id
    ).first()
    if _db_assignment is None:
        assignment = UserScope(scope_id=scope_id, user_id=user_id)
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    return _db_assignment


def remove_user_from_scope(db: Session, scope_id: int, user_id: int):
    assignment = UserScope(scope_id=scope_id, user_id=user_id)
    db.refresh(assignment)
    db.delete(assignment)
