"""Repository for flashcard persistence."""
from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from ..models.entities import Deck, Flashcard, ReviewLog


class FlashcardRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_decks(self, user_id: int) -> List[Deck]:
        return self.session.query(Deck).filter(Deck.user_id == user_id).all()

    def get_deck(self, user_id: int, deck_id: int) -> Optional[Deck]:
        return (
            self.session.query(Deck)
            .filter(Deck.user_id == user_id, Deck.id == deck_id)
            .one_or_none()
        )

    def create_deck(
        self, user_id: int, name: str, description: str = "", parent: Optional[Deck] = None
    ) -> Deck:
        deck = Deck(user_id=user_id, name=name, description=description, parent=parent)
        self.session.add(deck)
        self.session.flush()
        return deck

    def create_flashcard(
        self,
        *,
        user_id: int,
        deck_id: Optional[int],
        card_type: str,
        data: bytes,
        metadata: dict | None = None,
    ) -> Flashcard:
        card = Flashcard(
            user_id=user_id,
            deck_id=deck_id,
            card_type=card_type,
            data=data,
            metadata=metadata or {},
        )
        self.session.add(card)
        self.session.flush()
        return card

    def add_review_log(
        self,
        flashcard_id: int,
        *,
        scheduled_at,
        reviewed_at=None,
        rating: Optional[int] = None,
        interval: Optional[int] = None,
        ease_factor: Optional[float] = None,
    ) -> ReviewLog:
        log = ReviewLog(
            flashcard_id=flashcard_id,
            scheduled_at=scheduled_at,
            reviewed_at=reviewed_at,
            rating=rating,
            interval=interval,
            ease_factor=ease_factor,
        )
        self.session.add(log)
        self.session.flush()
        return log

    def get_flashcards(self, user_id: int) -> List[Flashcard]:
        return self.session.query(Flashcard).filter(Flashcard.user_id == user_id).all()

    def bulk_save(self, entities: Iterable[Flashcard | ReviewLog]) -> None:
        for entity in entities:
            self.session.add(entity)
