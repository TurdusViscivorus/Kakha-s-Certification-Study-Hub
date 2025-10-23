"""Business logic for flashcards and spaced repetition."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from typing import Iterable, List, Optional

from cryptography.fernet import Fernet

from ..database import session_scope
from ..repositories.flashcard_repository import FlashcardRepository


@dataclass
class FlashcardDTO:
    id: int
    deck_id: Optional[int]
    card_type: str
    content: dict
    metadata: dict


@dataclass
class ReviewOutcome:
    flashcard_id: int
    rating: int
    scheduled_at: dt.datetime
    interval: int
    ease_factor: float


class SM2Scheduler:
    """Simple implementation of the SM-2 spaced repetition algorithm."""

    def schedule(self, flashcard_id: int, reviews: List[ReviewOutcome], rating: int) -> ReviewOutcome:
        now = dt.datetime.utcnow()
        if not reviews:
            interval = 1 if rating >= 3 else 0
            ease = 2.5
        else:
            last = reviews[-1]
            ease = max(1.3, last.ease_factor + 0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
            if rating < 3:
                interval = 1
            elif last.interval == 0:
                interval = 1
            elif last.interval == 1:
                interval = 6
            else:
                interval = int(round(last.interval * ease))
        scheduled_at = now + dt.timedelta(days=interval)
        return ReviewOutcome(
            flashcard_id=flashcard_id,
            rating=rating,
            scheduled_at=scheduled_at,
            interval=interval,
            ease_factor=ease,
        )


class FlashcardService:
    def __init__(self, encryption_key: bytes) -> None:
        self._fernet = Fernet(encryption_key)

    def _encrypt_payload(self, payload: dict) -> bytes:
        return self._fernet.encrypt(json.dumps(payload).encode("utf-8"))

    def _decrypt_payload(self, blob: bytes) -> dict:
        return json.loads(self._fernet.decrypt(blob).decode("utf-8"))

    def create_deck(self, user_id: int, name: str, description: str = "", parent_id: Optional[int] = None) -> None:
        with session_scope() as session:
            repo = FlashcardRepository(session)
            parent = repo.get_deck(user_id, parent_id) if parent_id else None
            repo.create_deck(user_id, name, description, parent)

    def list_decks(self, user_id: int) -> List[dict]:
        with session_scope() as session:
            repo = FlashcardRepository(session)
            decks = repo.get_decks(user_id)
            return [
                {
                    "id": deck.id,
                    "name": deck.name,
                    "description": deck.description,
                    "parent_id": deck.parent_id,
                }
                for deck in decks
            ]

    def create_flashcard(
        self,
        *,
        user_id: int,
        deck_id: Optional[int],
        card_type: str,
        content: dict,
        metadata: Optional[dict] = None,
    ) -> FlashcardDTO:
        with session_scope() as session:
            repo = FlashcardRepository(session)
            encrypted = self._encrypt_payload(content)
            card = repo.create_flashcard(
                user_id=user_id,
                deck_id=deck_id,
                card_type=card_type,
                data=encrypted,
                metadata=metadata,
            )
            return FlashcardDTO(
                id=card.id,
                deck_id=card.deck_id,
                card_type=card.card_type,
                content=content,
                metadata=card.metadata_json,
            )

    def list_flashcards(self, user_id: int) -> List[FlashcardDTO]:
        with session_scope() as session:
            repo = FlashcardRepository(session)
            cards = repo.get_flashcards(user_id)
            results: List[FlashcardDTO] = []
            for card in cards:
                results.append(
                    FlashcardDTO(
                        id=card.id,
                        deck_id=card.deck_id,
                        card_type=card.card_type,
                        content=self._decrypt_payload(card.data),
                        metadata=card.metadata_json,
                    )
                )
            return results

    def schedule_review(
        self,
        *,
        user_id: int,
        flashcard_id: int,
        rating: int,
        scheduler: SM2Scheduler | None = None,
    ) -> ReviewOutcome:
        scheduler = scheduler or SM2Scheduler()
        with session_scope() as session:
            repo = FlashcardRepository(session)
            card = next(
                card for card in repo.get_flashcards(user_id) if card.id == flashcard_id
            )
            reviews = [
                ReviewOutcome(
                    flashcard_id=log.flashcard_id,
                    rating=log.rating or 0,
                    scheduled_at=log.scheduled_at,
                    interval=log.interval or 0,
                    ease_factor=float(log.ease_factor or 2.5),
                )
                for log in card.reviews
            ]
            outcome = scheduler.schedule(flashcard_id, reviews, rating)
            repo.add_review_log(
                flashcard_id=flashcard_id,
                scheduled_at=outcome.scheduled_at,
                reviewed_at=dt.datetime.utcnow(),
                rating=rating,
                interval=outcome.interval,
                ease_factor=outcome.ease_factor,
            )
            return outcome

    def bulk_import(
        self,
        *,
        user_id: int,
        cards: Iterable[dict],
    ) -> int:
        with session_scope() as session:
            repo = FlashcardRepository(session)
            count = 0
            for card in cards:
                payload = {
                    "front": card.get("front"),
                    "back": card.get("back"),
                    "extra": card.get("extra"),
                    "prompt": card.get("prompt"),
                }
                encrypted = self._encrypt_payload(payload)
                repo.create_flashcard(
                    user_id=user_id,
                    deck_id=card.get("deck_id"),
                    card_type=card.get("card_type", "basic"),
                    data=encrypted,
                    metadata=card.get("metadata") or {},
                )
                count += 1
            return count
