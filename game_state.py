"""Game state representations for Poker Coach."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List

from .card import Card


class Position(Enum):
    """Table positions with descriptive labels."""

    UTG = "Under the Gun"
    MP = "Middle Position"
    CO = "Cutoff"
    BTN = "Button"
    SB = "Small Blind"
    BB = "Big Blind"

    def __str__(self) -> str:  # pragma: no cover - convenience
        """Return the human-friendly position label."""
        return self.value


class Street(Enum):
    """Betting rounds of a Texas Hold'em hand."""

    PREFLOP = "Preflop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"

    def __str__(self) -> str:  # pragma: no cover - convenience
        """Return the human-friendly street name."""
        return self.value


@dataclass(slots=True)
class GameState:
    """Snapshot of the current poker hand context.

    Attributes:
        hole_cards: Hero hole cards (expected two, but validates content).
        board: Community cards revealed so far (0-5).
        street: Current betting street.
        pot_size: Total chips currently in the pot.
        bet_to_call: Chips required to continue in the hand.
        your_stack: Hero chip stack.
        opponent_stacks: Chip stacks for active opponents.
        your_position: Hero's table position.
        num_opponents: Total opponents at the table.
        active_opponents: Opponents still involved in the current hand.
        preflop_action: Ordered history of preflop actions as strings.
    """

    hole_cards: List[Card] = field(
        default_factory=list,
        metadata={"doc": "Hero hole cards (should contain exactly two Card instances)."},
    )
    board: List[Card] = field(
        default_factory=list,
        metadata={"doc": "Community cards on board (0 to 5 Card instances)."},
    )
    street: Street = field(
        default=Street.PREFLOP,
        metadata={"doc": "Current betting street of the hand."},
    )
    pot_size: float = field(
        default=0.0,
        metadata={"doc": "Total chips currently in the pot."},
    )
    bet_to_call: float = field(
        default=0.0,
        metadata={"doc": "Chip amount required to call and continue."},
    )
    your_stack: float = field(
        default=1000.0,
        metadata={"doc": "Hero chip stack at the start of the decision."},
    )
    opponent_stacks: List[float] = field(
        default_factory=list,
        metadata={"doc": "Stacks for each active opponent in the hand."},
    )
    your_position: Position = field(
        default=Position.BTN,
        metadata={"doc": "Hero's table position."},
    )
    num_opponents: int = field(
        default=5,
        metadata={"doc": "Total opponents seated at the table."},
    )
    active_opponents: int = field(
        default=5,
        metadata={"doc": "Number of opponents remaining in the current hand."},
    )
    preflop_action: List[str] = field(
        default_factory=list,
        metadata={"doc": "Chronological list of preflop actions taken so far."},
    )

    def __post_init__(self) -> None:
        """Run validations to ensure the state is internally consistent."""
        self._coerce_collections()
        self._validate_cards(self.hole_cards, max_allowed=2, label="hole cards")
        self._validate_cards(self.board, max_allowed=5, label="board cards")
        self._validate_no_duplicates()
        self._validate_numeric_fields()
        self._validate_actions()

    def _coerce_collections(self) -> None:
        """Ensure mutable collection fields use list instances."""
        object.__setattr__(self, "hole_cards", list(self.hole_cards))
        object.__setattr__(self, "board", list(self.board))
        object.__setattr__(self, "opponent_stacks", list(self.opponent_stacks))
        object.__setattr__(self, "preflop_action", list(self.preflop_action))

    @staticmethod
    def _validate_cards(cards: Iterable[Card], *, max_allowed: int, label: str) -> None:
        cards_list = list(cards)
        if len(cards_list) > max_allowed:
            raise ValueError(f"Too many {label}: expected at most {max_allowed}, got {len(cards_list)}.")
        for card in cards_list:
            if not isinstance(card, Card):
                raise TypeError(f"All {label} must be Card instances, got {type(card)!r}.")

    def _validate_no_duplicates(self) -> None:
        combined = self.hole_cards + self.board
        if len(combined) != len(set(combined)):
            raise ValueError("Duplicate cards detected between hole cards and board.")

    def _validate_numeric_fields(self) -> None:
        for numeric_name in ("pot_size", "bet_to_call", "your_stack"):
            value = getattr(self, numeric_name)
            if value < 0:
                raise ValueError(f"{numeric_name} must be non-negative, got {value}.")

        for index, stack in enumerate(self.opponent_stacks):
            if stack < 0:
                raise ValueError(f"Opponent stack at index {index} must be non-negative, got {stack}.")

        if self.num_opponents < 0:
            raise ValueError("num_opponents must be non-negative.")
        if self.active_opponents < 0:
            raise ValueError("active_opponents must be non-negative.")
        if self.active_opponents > self.num_opponents:
            raise ValueError("active_opponents cannot exceed num_opponents.")

    def _validate_actions(self) -> None:
        if not all(isinstance(action, str) for action in self.preflop_action):
            raise TypeError("preflop_action must contain only string entries.")

    @property
    def pot_odds(self) -> float:
        """Return the fraction representing pot odds for the current decision."""
        if self.bet_to_call <= 0:
            return 0.0
        total = self.pot_size + self.bet_to_call
        if total <= 0:
            return 0.0
        return self.bet_to_call / total

    @property
    def effective_stack(self) -> float:
        """Return the smallest stack between hero and opponents."""
        stacks = [self.your_stack] + self.opponent_stacks
        return min(stacks) if stacks else 0.0
