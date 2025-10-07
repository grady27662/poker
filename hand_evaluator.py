"""Hand evaluation utilities built on top of treys.

The treys library uses an inverted ranking system where *lower* numerical values
represent stronger hands (1 == Royal Flush, 7462 == worst High Card).
"""

from __future__ import annotations

from typing import Iterable, List, Sequence

from treys import Card as TreysCard
from treys import Evaluator

from src.models.card import Card

__all__ = ["HandEvaluator"]


class HandEvaluator:
    """Evaluate poker hands using the treys Evaluator."""

    def __init__(self) -> None:
        """Construct a new evaluator instance."""
        self._evaluator = Evaluator()

    def _convert_to_treys(self, card: Card) -> int:
        """Convert a :class:`Card` into the treys integer representation."""
        if not isinstance(card, Card):
            raise TypeError(f"Expected Card instance, got {type(card)!r}.")

        rank_str = card.rank.short_name.upper()
        suit_str = card.suit.short_name.lower()
        card_str = f"{rank_str}{suit_str}"

        return TreysCard.new(card_str)

    @staticmethod
    def _ensure_no_duplicates(cards: Iterable[Card]) -> None:
        """Validate that no duplicate cards exist in the provided iterable."""
        seen: set[str] = set()
        for card in cards:
            if not isinstance(card, Card):
                raise TypeError(f"Expected Card instance, got {type(card)!r}.")
            rep = str(card)
            if rep in seen:
                raise ValueError(f"Duplicate card detected: {rep}.")
            seen.add(rep)

    def evaluate_hand(self, hole_cards: Sequence[Card], board: Sequence[Card]) -> int:
        """Evaluate a Hold'em hand and return the treys rank (lower is better).

        Args:
            hole_cards: Hero cards (exactly two).
            board: Community cards (0-5).

        Returns:
            Integer hand rank where 1 is best and 7462 is worst.

        Raises:
            ValueError: If card counts are invalid or duplicates are detected.
            TypeError: If inputs are not sequences of :class:`Card`.
        """
        hole_cards_list = list(hole_cards)
        board_list = list(board)

        if len(hole_cards_list) != 2:
            raise ValueError(f"Hole cards must contain exactly two cards, got {len(hole_cards_list)}.")
        if len(board_list) > 5:
            raise ValueError(f"Board cannot contain more than five cards, got {len(board_list)}.")

        self._ensure_no_duplicates(hole_cards_list + board_list)

        treys_hole = [self._convert_to_treys(card) for card in hole_cards_list]
        treys_board = [self._convert_to_treys(card) for card in board_list]

        return self._evaluator.evaluate(treys_board, treys_hole)

    def get_hand_class(self, rank: int) -> str:
        """Translate a treys rank into a human-readable hand class."""
        if not isinstance(rank, int):
            raise TypeError(f"Hand rank must be an integer, got {type(rank)!r}.")
        if rank < 1:
            raise ValueError(f"Hand rank must be positive, got {rank}.")

        rank_class = self._evaluator.get_rank_class(rank)
        return self._evaluator.class_to_string(rank_class)
