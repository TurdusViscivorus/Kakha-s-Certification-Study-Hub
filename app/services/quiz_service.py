"""Quiz generation and grading services."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from cryptography.fernet import Fernet

from ..database import session_scope
from ..repositories.quiz_repository import QuizRepository


@dataclass
class QuizQuestionDTO:
    id: int
    question_type: str
    prompt: dict
    answer: dict
    explanation: dict
    references: list
    metadata: dict


@dataclass
class QuizAttemptResult:
    attempt_id: int
    score: float
    responses: List[dict]


class QuizService:
    def __init__(self, encryption_key: bytes) -> None:
        self._fernet = Fernet(encryption_key)

    def _encrypt(self, payload: dict) -> bytes:
        return self._fernet.encrypt(json.dumps(payload).encode("utf-8"))

    def _decrypt(self, blob: bytes) -> dict:
        return json.loads(self._fernet.decrypt(blob).decode("utf-8"))

    def add_blueprint(
        self,
        *,
        user_id: int,
        name: str,
        description: str,
        metadata: dict,
        sections: Iterable[tuple[str, float]],
    ) -> int:
        with session_scope() as session:
            repo = QuizRepository(session)
            blueprint = repo.create_blueprint(
                user_id=user_id, name=name, description=description, metadata=metadata
            )
            for section_name, weight in sections:
                repo.add_section(blueprint, section_name, weight)
            return blueprint.id

    def add_question(
        self,
        *,
        user_id: int,
        blueprint_section_id: Optional[int],
        question_type: str,
        prompt: dict,
        answer: dict,
        explanation: dict,
        references: list,
        metadata: dict,
    ) -> int:
        with session_scope() as session:
            repo = QuizRepository(session)
            question = repo.add_question(
                user_id=user_id,
                blueprint_section_id=blueprint_section_id,
                question_type=question_type,
                prompt=self._encrypt(prompt),
                answer=self._encrypt(answer),
                explanation=self._encrypt(explanation),
                references=references,
                metadata=metadata,
            )
            return question.id

    def list_questions(self, user_id: int) -> List[QuizQuestionDTO]:
        with session_scope() as session:
            repo = QuizRepository(session)
            return [
                QuizQuestionDTO(
                    id=q.id,
                    question_type=q.question_type,
                    prompt=self._decrypt(q.prompt),
                    answer=self._decrypt(q.answer),
                    explanation=self._decrypt(q.explanation) if q.explanation else {},
                    references=q.references or [],
                    metadata=q.metadata_json or {},
                )
                for q in repo.list_questions(user_id)
            ]

    def generate_exam(
        self,
        *,
        user_id: int,
        blueprint_id: Optional[int],
        mode: str,
        question_pool: List[QuizQuestionDTO],
        count: int,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[QuizQuestionDTO]:
        if not question_pool:
            return []
        if weights:
            weighted_questions: List[QuizQuestionDTO] = []
            for question in question_pool:
                section = question.metadata.get("section")
                weight = weights.get(section, 1.0) if section else 1.0
                weighted_questions.extend([question] * max(1, int(weight * 10)))
            return random.sample(weighted_questions, min(count, len(weighted_questions)))
        return random.sample(question_pool, min(count, len(question_pool)))

    def grade_attempt(
        self,
        *,
        user_id: int,
        blueprint_id: Optional[int],
        mode: str,
        responses: List[dict],
    ) -> QuizAttemptResult:
        graded: List[tuple[dict, bool]] = []
        for response in responses:
            answer_payload = response["answer"]
            user_answer = response["user_answer"]
            question_type = response.get("question_type", "mcq")
            is_correct = False
            if question_type in {"mcq", "multi", "ordering", "matching"}:
                is_correct = sorted(answer_payload) == sorted(user_answer)
            elif question_type == "numeric":
                try:
                    is_correct = float(answer_payload) == float(user_answer)
                except (TypeError, ValueError):
                    is_correct = False
            elif question_type == "short":
                expected = str(answer_payload).strip().lower()
                actual = str(user_answer).strip().lower()
                is_correct = expected == actual
            else:
                expected = str(answer_payload).strip().lower()
                actual = str(user_answer).strip().lower()
                is_correct = expected in actual or actual in expected
            graded.append((response, is_correct))
        correct = sum(1 for _, flag in graded if flag)
        score = (correct / len(graded)) * 100 if graded else 0.0
        encoded_responses = [
            {
                "question_id": item["question_id"],
                "user_answer": self._encrypt({"value": item["user_answer"]}),
                "is_correct": flag,
                "confidence": item.get("confidence"),
            }
            for item, flag in graded
        ]
        with session_scope() as session:
            repo = QuizRepository(session)
            attempt = repo.record_attempt(
                user_id=user_id,
                blueprint_id=blueprint_id,
                mode=mode,
                score=score,
                responses=encoded_responses,
            )
        return QuizAttemptResult(attempt_id=attempt.id, score=score, responses=encoded_responses)
