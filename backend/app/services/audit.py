from sqlalchemy.orm import Session
from ..models.audit import AuditLog, AuditAction
from ..models.user import User
import json


class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: AuditAction,
        entity_type: str,
        entity_id: int,
        user: User,
        old_value: dict = None,
        new_value: dict = None
    ):
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user.id,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
        )
        db.add(log)
        db.commit()
        return log
