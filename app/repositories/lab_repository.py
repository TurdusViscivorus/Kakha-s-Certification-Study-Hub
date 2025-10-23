"""Repository for lab checklist data."""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..models.entities import LabChecklist, LabTask


class LabRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_checklist(self, user_id: int, name: str, description: str) -> LabChecklist:
        checklist = LabChecklist(user_id=user_id, name=name, description=description)
        self.session.add(checklist)
        self.session.flush()
        return checklist

    def add_task(
        self, checklist: LabChecklist, name: str, status: str = "To-do", notes: bytes | None = None
    ) -> LabTask:
        task = LabTask(checklist=checklist, name=name, status=status, notes=notes)
        self.session.add(task)
        self.session.flush()
        return task

    def get_checklist(self, checklist_id: int) -> LabChecklist | None:
        return self.session.query(LabChecklist).filter(LabChecklist.id == checklist_id).one_or_none()

    def list_checklists(self, user_id: int) -> List[LabChecklist]:
        return self.session.query(LabChecklist).filter(LabChecklist.user_id == user_id).all()
