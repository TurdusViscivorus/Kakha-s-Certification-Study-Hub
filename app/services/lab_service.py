"""Manage lab checklists and attachments."""
from __future__ import annotations

import base64
import json
from typing import List

from cryptography.fernet import Fernet

from ..database import session_scope
from ..repositories.lab_repository import LabRepository


class LabService:
    def __init__(self, encryption_key: bytes) -> None:
        self._fernet = Fernet(encryption_key)

    def _encrypt(self, payload: dict) -> bytes:
        return self._fernet.encrypt(json.dumps(payload).encode("utf-8"))

    def _decrypt(self, blob: bytes) -> dict:
        return json.loads(self._fernet.decrypt(blob).decode("utf-8"))

    def create_checklist(self, user_id: int, name: str, description: str) -> int:
        with session_scope() as session:
            repo = LabRepository(session)
            checklist = repo.create_checklist(user_id, name, description)
            return checklist.id

    def add_task(self, checklist_id: int, name: str, status: str = "To-do", notes: str = "") -> int:
        with session_scope() as session:
            repo = LabRepository(session)
            checklist = repo.get_checklist(checklist_id)
            if checklist is None:
                raise ValueError("Checklist not found")
            task = repo.add_task(checklist, name, status, self._encrypt({"notes": notes}))
            return task.id

    def list_checklists(self, user_id: int) -> List[dict]:
        with session_scope() as session:
            repo = LabRepository(session)
            checklists = repo.list_checklists(user_id)
            return [
                {
                    "id": checklist.id,
                    "name": checklist.name,
                    "description": checklist.description,
                    "tasks": [
                        {
                            "id": task.id,
                            "name": task.name,
                            "status": task.status,
                            "notes": self._decrypt(task.notes or self._encrypt({"notes": ""}))["notes"],
                            "attachments": [
                                {
                                    "id": attachment.id,
                                    "filename": attachment.filename,
                                    "blob": base64.b64encode(attachment.blob).decode("utf-8"),
                                }
                                for attachment in task.attachments
                            ],
                        }
                        for task in checklist.tasks
                    ],
                }
                for checklist in checklists
            ]
