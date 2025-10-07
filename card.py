"""Card model definitions and helpers for Poker Coach."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Dict


class Suit(Enum):
    """Enumeration of card suits with human-friendly symbols."""

    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"

    @property
    def symbol(self) -> str:
        """Return the Unicode symbol for the suit."""
        return self.value

    @property
    def short_name(self) -> str:
        """Return the short single-letter identifier for the suit."""
        return _SUIT_SHORT_NAMES[self]

    @classmethod
    def from_string(cls, value: str) -> "Suit":
        """Create a suit from a single-character identifier or symbol."""
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Suit string cannot be empty.")

        for suit in cls:
            if normalized in {suit.symbol.lower(), suit.short_name}:
                return suit

        raise ValueError(f"Invalid suit string: {value!r}")


class Rank(IntEnum):
    """Enumeration of card ranks with their numeric ordering."""

    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def short_name(self) -> str:
        """Return the canonical one-character representation of the rank."""
        return _RANK_DISPLAY[self]

    @classmethod
    def from_string(cls, value: str) -> "Rank":
        """Create a rank from a single-character or numeric string."""
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Rank string cannot be empty.")

        face_cards = {display: rank for rank, display in _RANK_DISPLAY.items()}

        if normalized in face_cards:
            return face_cards[normalized]

        try:
            numeric = int(normalized)
        except ValueError as exc:
            raise ValueError(f"Invalid rank string: {value!r}") from exc

        try:
            return cls(numeric)
        except ValueError as exc:
            raise ValueError(f"Rank value out of bounds: {numeric}") from exc


@dataclass(frozen=True, slots=True)
class Card:
    """Card representation with rank and suit."""

    rank: Rank
    suit: Suit

    def __post_init__(self) -> None:
        """Validate that rank and suit are correctly typed."""
        if not isinstance(self.rank, Rank):
            raise TypeError(f"rank must be a Rank enum, got {type(self.rank)!r}")
        if not isinstance(self.suit, Suit):
            raise TypeError(f"suit must be a Suit enum, got {type(self.suit)!r}")

    def __str__(self) -> str:
        """Return the canonical shorthand such as 'As' or 'Td'."""
        return f"{self.rank.short_name}{self.suit.short_name}"

    @classmethod
    def from_string(cls, card_str: str) -> "Card":
        """Parse a shorthand string (e.g. 'As', 'td', '10h') into a Card."""
        if not card_str:
            raise ValueError("Card string cannot be empty.")

        stripped = card_str.strip()
        if len(stripped) < 2:
            raise ValueError(f"Invalid card string: {card_str!r}")

        rank_part = stripped[:-1]
        suit_part = stripped[-1]

        rank = Rank.from_string(rank_part)
        suit = Suit.from_string(suit_part)

        return cls(rank=rank, suit=suit)


_SUIT_SHORT_NAMES: Dict[Suit, str] = {
    Suit.SPADES: "s",
    Suit.HEARTS: "h",
    Suit.DIAMONDS: "d",
    Suit.CLUBS: "c",
}

_RANK_DISPLAY: Dict[Rank, str] = {
    Rank.TWO: "2",
    Rank.THREE: "3",
    Rank.FOUR: "4",
    Rank.FIVE: "5",
    Rank.SIX: "6",
    Rank.SEVEN: "7",
    Rank.EIGHT: "8",
    Rank.NINE: "9",
    Rank.TEN: "T",
    Rank.JACK: "J",
    Rank.QUEEN: "Q",
    Rank.KING: "K",
    Rank.ACE: "A",
}
