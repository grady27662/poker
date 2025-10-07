"""Action definitions and recommendation data structures for Poker Coach."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """Supported player actions for decision-making."""

    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"

    def __str__(self) -> str:  # pragma: no cover - convenience
        """Return the lowercase action keyword."""
        return self.value


@dataclass(slots=True, frozen=True)
class ActionRecommendation:
    """Structured output from the decision engine.

    Attributes:
        action: Recommended poker action.
        confidence: Confidence score between 0.0 and 1.0.
        rationale: Human-readable explanation for the recommendation.
    """

    action: ActionType
    confidence: float
    rationale: str

    def __post_init__(self) -> None:
        """Validate recommendation data."""
        if not isinstance(self.action, ActionType):
            raise TypeError(f"action must be an ActionType, got {type(self.action)!r}")

        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0.")

        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be a non-empty string.")
