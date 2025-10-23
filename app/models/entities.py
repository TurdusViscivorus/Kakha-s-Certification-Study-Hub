"""SQLAlchemy models for Kakha's Certification Study Hub."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    password_salt = Column(LargeBinary(64), nullable=False)
    encryption_blob = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    hello_enabled = Column(Boolean, default=False)

    decks = relationship("Deck", back_populates="user", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="user", cascade="all, delete-orphan")
    quiz_blueprints = relationship(
        "ExamBlueprint", back_populates="user", cascade="all, delete-orphan"
    )
    lab_checklists = relationship(
        "LabChecklist", back_populates="user", cascade="all, delete-orphan"
    )
    content_packs = relationship(
        "ContentPack", back_populates="user", cascade="all, delete-orphan"
    )


class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    parent_id = Column(Integer, ForeignKey("decks.id"))
    description = Column(Text)

    user = relationship("User", back_populates="decks")
    parent = relationship("Deck", remote_side=[id])
    children = relationship("Deck", back_populates="parent")
    flashcards = relationship("Flashcard", back_populates="deck", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tag_user"),)


class DeckTag(Base):
    __tablename__ = "deck_tags"

    deck_id = Column(Integer, ForeignKey("decks.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    deck_id = Column(Integer, ForeignKey("decks.id", ondelete="CASCADE"))
    card_type = Column(String(32), nullable=False)
    data = Column(LargeBinary, nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    user = relationship("User", back_populates="flashcards")
    deck = relationship("Deck", back_populates="flashcards")
    reviews = relationship("ReviewLog", back_populates="flashcard", cascade="all, delete-orphan")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True)
    flashcard_id = Column(Integer, ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime)
    rating = Column(Integer)
    interval = Column(Integer)
    ease_factor = Column(Numeric(5, 2))

    flashcard = relationship("Flashcard", back_populates="reviews")


class ExamBlueprint(Base):
    __tablename__ = "exam_blueprints"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    metadata = Column(JSON, default=dict)

    user = relationship("User", back_populates="quiz_blueprints")
    sections = relationship(
        "BlueprintSection", back_populates="blueprint", cascade="all, delete-orphan"
    )


class BlueprintSection(Base):
    __tablename__ = "blueprint_sections"

    id = Column(Integer, primary_key=True)
    blueprint_id = Column(
        Integer, ForeignKey("exam_blueprints.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(128), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)

    blueprint = relationship("ExamBlueprint", back_populates="sections")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blueprint_section_id = Column(Integer, ForeignKey("blueprint_sections.id"))
    question_type = Column(String(32), nullable=False)
    prompt = Column(LargeBinary, nullable=False)
    answer = Column(LargeBinary, nullable=False)
    explanation = Column(LargeBinary)
    references = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blueprint_id = Column(Integer, ForeignKey("exam_blueprints.id"))
    mode = Column(String(32), nullable=False)
    started_at = Column(DateTime, default=dt.datetime.utcnow)
    completed_at = Column(DateTime)
    score = Column(Numeric(5, 2))

    responses = relationship(
        "QuizResponse", back_populates="attempt", cascade="all, delete-orphan"
    )


class QuizResponse(Base):
    __tablename__ = "quiz_responses"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id"), nullable=False)
    user_answer = Column(LargeBinary, nullable=False)
    is_correct = Column(Boolean, default=False)
    confidence = Column(Integer)

    attempt = relationship("QuizAttempt", back_populates="responses")
    question = relationship("QuizQuestion")


class StudyDay(Base):
    __tablename__ = "study_days"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, default=dt.date.today, nullable=False)
    minutes_spent = Column(Integer, default=0)
    cards_reviewed = Column(Integer, default=0)
    quizzes_completed = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_study_day"),)


class LabChecklist(Base):
    __tablename__ = "lab_checklists"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)

    user = relationship("User", back_populates="lab_checklists")
    tasks = relationship("LabTask", back_populates="checklist", cascade="all, delete-orphan")


class LabTask(Base):
    __tablename__ = "lab_tasks"

    id = Column(Integer, primary_key=True)
    checklist_id = Column(
        Integer, ForeignKey("lab_checklists.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(128), nullable=False)
    status = Column(String(16), default="To-do")
    notes = Column(LargeBinary)

    checklist = relationship("LabChecklist", back_populates="tasks")
    attachments = relationship(
        "Attachment", back_populates="task", cascade="all, delete-orphan"
    )


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("lab_tasks.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    blob = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    task = relationship("LabTask", back_populates="attachments")


class ContentPack(Base):
    __tablename__ = "content_packs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(128), nullable=False)
    version = Column(String(32), nullable=False)
    checksum = Column(String(128), nullable=False)
    metadata = Column(JSON, default=dict)
    manifest = Column(LargeBinary, nullable=False)
    installed_at = Column(DateTime, default=dt.datetime.utcnow)

    user = relationship("User", back_populates="content_packs")


__all__ = [name for name in globals() if name[0].isupper()]
