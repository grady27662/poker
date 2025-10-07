"""Pre-flop ranges and strategy utilities."""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterable

from src.models.card import Card
from src.models.game_state import Position

__all__ = ["PreflopRanges"]


_UTG_OPENING = frozenset(
    {
        "AA",
        "KK",
        "QQ",
        "JJ",
        "TT",
        "99",
        "AKs",
        "AQs",
        "AJs",
        "ATs",
        "AKo",
        "AQo",
        "KQs",
    }
)

_MP_ADDITIONS = {
    "88",
    "77",
    "A9s",
    "A8s",
    "AJo",
    "KJs",
    "KTs",
    "QJs",
}

_CO_ADDITIONS = {
    "66",
    "55",
    "ATo",
    "KQo",
    "QTs",
    "JTs",
    "T9s",
    "A7s",
    "A6s",
    "A5s",
    "A4s",
    "A3s",
    "A2s",
}

_ALL_PAIRS = {pair for pair in ("AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22")}

_BROADWAY_SUITS = {
    "AKs",
    "AQs",
    "AJs",
    "ATs",
    "KQs",
    "KJs",
    "QJs",
    "JTs",
    "KTs",
    "QTs",
    "J9s",
    "T9s",
    "98s",
    "87s",
    "76s",
    "65s",
    "54s",
}

_BROADWAY_OFFSUIT = {
    "AKo",
    "AQo",
    "AJo",
    "ATo",
    "KQo",
    "KJo",
    "QJo",
    "JTo",
}

_SUITED_ACES = {
    "A9s",
    "A8s",
    "A7s",
    "A6s",
    "A5s",
    "A4s",
    "A3s",
    "A2s",
}

_SB_EXTRA = {
    "KTo",
    "QTo",
    "JTo",
    "T9o",
    "98o",
    "A9o",
    "A8o",
    "K9s",
    "Q9s",
    "J8s",
    "T8s",
    "97s",
    "86s",
    "75s",
}

_BB_EXTRA = {
    "A7o",
    "A6o",
    "A5o",
    "A4o",
    "A3o",
    "A2o",
    "K9o",
    "Q9o",
    "J9o",
    "T8o",
    "97o",
    "86o",
    "76o",
    "65o",
}


def _normalize_combo_literal(hand: str) -> str:
    cleaned = hand.strip()
    if len(cleaned) == 2:
        return cleaned.upper()
    if len(cleaned) == 3:
        return f"{cleaned[:2].upper()}{cleaned[2].lower()}"
    raise ValueError(f"Invalid combo representation: {hand!r}")


def _freeze(values: Iterable[str]) -> FrozenSet[str]:
    """Return a normalized combo set using canonical formatting."""
    return frozenset(_normalize_combo_literal(value) for value in values)


class PreflopRanges:
    """Simplified GTO-inspired pre-flop ranges by position.

    These ranges approximate common opening frequencies:
        * UTG ~15%
        * MP ~20%
        * CO ~25%
        * BTN ~45%
        * SB ~35%
        * BB ~60% (defesa contra steals)
    """

    OPENING_RANGES: Dict[Position, FrozenSet[str]] = {
        Position.UTG: _UTG_OPENING,
        Position.MP: _freeze(set(_UTG_OPENING) | _MP_ADDITIONS),
        Position.CO: _freeze(set(_UTG_OPENING) | _MP_ADDITIONS | _CO_ADDITIONS),
        Position.BTN: _freeze(_ALL_PAIRS | _BROADWAY_SUITS | _BROADWAY_OFFSUIT | _SUITED_ACES),
        Position.SB: _freeze(
            _ALL_PAIRS
            | _BROADWAY_SUITS
            | _BROADWAY_OFFSUIT
            | _SUITED_ACES
            | _SB_EXTRA
        ),
        Position.BB: _freeze(
            _ALL_PAIRS
            | _BROADWAY_SUITS
            | _BROADWAY_OFFSUIT
            | _SUITED_ACES
            | _SB_EXTRA
            | _BB_EXTRA
        ),
    }

    THREE_BET_RANGES: Dict[Position, FrozenSet[str]] = {
        Position.UTG: _freeze({"AA", "KK", "QQ", "AKs", "AKo"}),
        Position.MP: _freeze({"AA", "KK", "QQ", "JJ", "AKs", "AQs", "AKo"}),
        Position.CO: _freeze({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AKo"}),
        Position.BTN: _freeze({"AA", "KK", "QQ", "JJ", "TT", "99", "AKs", "AQs", "A5s", "KQs", "AKo"}),
        Position.SB: _freeze({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AKo", "A5s", "KQs"}),
        Position.BB: _freeze({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AKo", "A5s", "KQs"}),
    }

    @staticmethod
    def normalize_hand(card1_str: str, card2_str: str) -> str:
        """Return a canonical combo string such as ``AKs`` or ``77``.

        Examples:
            >>> PreflopRanges.normalize_hand("Ks", "Ad")
            'AKo'
            >>> PreflopRanges.normalize_hand("7h", "7d")
            '77'
        """
        card1 = Card.from_string(card1_str)
        card2 = Card.from_string(card2_str)

        rank1 = card1.rank.short_name.upper()
        rank2 = card2.rank.short_name.upper()

        if rank1 == rank2:
            return f"{rank1}{rank2}"

        high, low = sorted((card1, card2), key=lambda c: c.rank, reverse=True)
        suffix = "s" if high.suit == low.suit else "o"
        return f"{high.rank.short_name.upper()}{low.rank.short_name.upper()}{suffix}"

    @classmethod
    def should_open(cls, hand: str, position: Position) -> bool:
        """Return ``True`` if a normalized combo should be opened from position."""
        if position not in cls.OPENING_RANGES:
            raise ValueError(f"Unknown position: {position}")
        normalized = cls._normalize_combo_str(hand)
        return normalized in cls.OPENING_RANGES[position]

    @classmethod
    def should_3bet(cls, hand: str, position: Position) -> bool:
        """Return ``True`` if combo is considered a value/bluff 3-bet."""
        if position not in cls.THREE_BET_RANGES:
            raise ValueError(f"Unknown position: {position}")
        normalized = cls._normalize_combo_str(hand)
        return normalized in cls.THREE_BET_RANGES[position]

    @staticmethod
    def _normalize_combo_str(hand: str) -> str:
        return _normalize_combo_literal(hand)
