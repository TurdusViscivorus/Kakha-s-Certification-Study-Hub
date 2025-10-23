"""Repository for quiz and exam related data."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.entities import BlueprintSection, ExamBlueprint, QuizAttempt, QuizQuestion, QuizResponse


class QuizRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_blueprint(
        self, *, user_id: int, name: str, description: str, metadata: dict
    ) -> ExamBlueprint:
        blueprint = ExamBlueprint(
            user_id=user_id,
            name=name,
            description=description,
            metadata_json=metadata,
        )
        self.session.add(blueprint)
        self.session.flush()
        return blueprint

    def add_section(
        self, blueprint: ExamBlueprint, name: str, weight: float
    ) -> BlueprintSection:
        section = BlueprintSection(blueprint=blueprint, name=name, weight=weight)
        self.session.add(section)
        self.session.flush()
        return section

    def add_question(
        self,
        *,
        user_id: int,
        blueprint_section_id: Optional[int],
        question_type: str,
        prompt: bytes,
        answer: bytes,
        explanation: bytes,
        references: list,
        metadata: dict,
    ) -> QuizQuestion:
        question = QuizQuestion(
            user_id=user_id,
            blueprint_section_id=blueprint_section_id,
            question_type=question_type,
            prompt=prompt,
            answer=answer,
            explanation=explanation,
            references=references,
            metadata_json=metadata,
        )
        self.session.add(question)
        self.session.flush()
        return question

    def record_attempt(
        self,
        *,
        user_id: int,
        blueprint_id: Optional[int],
        mode: str,
        score: float,
        responses: List[dict],
    ) -> QuizAttempt:
        attempt = QuizAttempt(user_id=user_id, blueprint_id=blueprint_id, mode=mode, score=score)
        self.session.add(attempt)
        self.session.flush()
        for response in responses:
            db_response = QuizResponse(
                attempt_id=attempt.id,
                question_id=response["question_id"],
                user_answer=response["user_answer"],
                is_correct=response.get("is_correct", False),
                confidence=response.get("confidence"),
            )
            self.session.add(db_response)
        self.session.flush()
        return attempt

    def list_questions(self, user_id: int) -> List[QuizQuestion]:
        return self.session.query(QuizQuestion).filter(QuizQuestion.user_id == user_id).all()
