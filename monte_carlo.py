"""Monte Carlo equity simulation engine for Poker Coach."""

from __future__ import annotations

import random
from typing import Iterable, List, Sequence

from src.engine.hand_evaluator import HandEvaluator
from src.models.card import Card, Rank, Suit

__all__ = ["MonteCarloSimulator"]


class MonteCarloSimulator:
    """Run Monte Carlo simulations to estimate hand equity.

    The algorithm repeatedly completes the board and deals opponent hands with
    random cards, evaluates each showdown and tallies wins/ties for the hero.
    """

    def __init__(self, num_simulations: int = 10_000, *, rng: random.Random | None = None) -> None:
        if num_simulations <= 0:
            raise ValueError("num_simulations must be positive.")
        self.num_simulations = num_simulations
        self._evaluator = HandEvaluator()
        self._rng = rng or random.Random()

    def create_deck(self, exclude_cards: Sequence[Card]) -> List[Card]:
        """Return a deck of 52 cards minus the exclusions."""
        exclude_list = list(exclude_cards)
        self._validate_cards(exclude_list, label="exclude_cards")
        self._ensure_unique(exclude_list, label="exclude_cards")

        excluded = {str(card) for card in exclude_list}
        deck = [Card(rank=rank, suit=suit) for rank in Rank for suit in Suit]
        return [card for card in deck if str(card) not in excluded]

    def simulate_equity(
        self,
        hero_cards: Sequence[Card],
        board: Sequence[Card],
        num_opponents: int = 1,
    ) -> float:
        """Return hero equity estimate using Monte Carlo simulation.

        Steps per simulation:
            1. Generate a deck excluding known cards.
            2. Shuffle the deck uniformly at random.
            3. Complete the board to five cards with random draws.
            4. Deal two hole cards to each opponent.
            5. Compare treys hand ranks where lower values are better.

        Equity is calculated as ``(wins + ties * 0.5) / num_simulations``.
        """
        hero_cards_list = list(hero_cards)
        board_list = list(board)

        self._validate_cards(hero_cards_list, label="hero_cards")
        self._validate_cards(board_list, label="board", max_length=5)

        if len(hero_cards_list) != 2:
            raise ValueError("hero_cards must contain exactly two cards.")
        if len(board_list) > 5:
            raise ValueError("board cannot contain more than five cards.")
        if num_opponents < 1:
            raise ValueError("num_opponents must be at least 1.")

        combined = hero_cards_list + board_list
        self._ensure_unique(combined, label="input cards")

        base_deck = self.create_deck(combined)
        cards_needed = max(0, 5 - len(board_list)) + num_opponents * 2
        if len(base_deck) < cards_needed:
            raise ValueError("Not enough cards remaining to complete the simulation.")

        wins = 0
        ties = 0

        for _ in range(self.num_simulations):
            deck = base_deck[:]
            self._rng.shuffle(deck)

            sim_board = board_list[:]
            board_needed = 5 - len(sim_board)
            if board_needed > 0:
                sim_board.extend(deck[:board_needed])
                del deck[:board_needed]

            hero_rank = self._evaluator.evaluate_hand(hero_cards_list, sim_board)

            opponent_ranks = []
            for opponent in range(num_opponents):
                if len(deck) < 2:
                    raise ValueError("Deck exhausted while dealing opponent hands.")
                opponent_hand = deck[:2]
                del deck[:2]
                opponent_rank = self._evaluator.evaluate_hand(opponent_hand, sim_board)
                opponent_ranks.append(opponent_rank)

            best_opponent_rank = min(opponent_ranks)
            if hero_rank < best_opponent_rank:
                wins += 1
            elif hero_rank == best_opponent_rank:
                ties += 1

        return (wins + 0.5 * ties) / self.num_simulations

    @staticmethod
    def _validate_cards(cards: Iterable[Card], *, label: str, max_length: int | None = None) -> None:
        cards_list = list(cards)
        if max_length is not None and len(cards_list) > max_length:
            raise ValueError(f"{label} cannot contain more than {max_length} cards.")
        for card in cards_list:
            if not isinstance(card, Card):
                raise TypeError(f"All entries in {label} must be Card instances, got {type(card)!r}.")

    @staticmethod
    def _ensure_unique(cards: Iterable[Card], *, label: str) -> None:
        cards_list = list(cards)
        seen = {str(card) for card in cards_list}
        if len(cards_list) != len(seen):
            raise ValueError(f"Duplicate cards detected in {label}.")
