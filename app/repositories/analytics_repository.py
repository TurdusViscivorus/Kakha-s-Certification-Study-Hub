"""Repository helpers for analytics."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..models.entities import QuizAttempt, QuizResponse, StudyDay


class AnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_study_day(
        self,
        *,
        user_id: int,
        date: dt.date,
        minutes_spent: int,
        cards_reviewed: int,
        quizzes_completed: int,
    ) -> StudyDay:
        study_day = (
            self.session.query(StudyDay)
            .filter(StudyDay.user_id == user_id, StudyDay.date == date)
            .one_or_none()
        )
        if study_day is None:
            study_day = StudyDay(
                user_id=user_id,
                date=date,
                minutes_spent=minutes_spent,
                cards_reviewed=cards_reviewed,
                quizzes_completed=quizzes_completed,
            )
            self.session.add(study_day)
        else:
            study_day.minutes_spent += minutes_spent
            study_day.cards_reviewed += cards_reviewed
            study_day.quizzes_completed += quizzes_completed
        self.session.flush()
        return study_day

    def get_study_days(self, user_id: int, *, days: int = 365) -> List[StudyDay]:
        cutoff = dt.date.today() - dt.timedelta(days=days)
        return (
            self.session.query(StudyDay)
            .filter(StudyDay.user_id == user_id, StudyDay.date >= cutoff)
            .order_by(StudyDay.date)
            .all()
        )

    def get_recent_quiz_attempts(self, user_id: int, limit: int = 50) -> List[QuizAttempt]:
        return (
            self.session.query(QuizAttempt)
            .options(selectinload(QuizAttempt.responses).selectinload(QuizResponse.question))
            .filter(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.started_at.desc())
            .limit(limit)
            .all()
        )

    def average_score(self, user_id: int) -> Optional[float]:
        result = self.session.query(func.avg(QuizAttempt.score)).filter(QuizAttempt.user_id == user_id).scalar()
        return float(result) if result is not None else None
