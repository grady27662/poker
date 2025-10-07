"""Odds and expected value calculations for Poker Coach."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.game_state import GameState

__all__ = ["OddsCalculator"]


@dataclass(slots=True)
class OddsCalculator:
    """Collection of poker odds formulas.

    The calculator is stateless and can be reused across evaluations.
    """

    def calculate_pot_odds(self, game_state: GameState) -> float:
        """Return pot odds as ``bet_to_call / (pot_size + bet_to_call)``."""
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState instance.")

        bet_to_call = max(game_state.bet_to_call, 0.0)
        if bet_to_call == 0:
            return 0.0

        pot_size = max(game_state.pot_size, 0.0)
        denominator = pot_size + bet_to_call
        if denominator <= 0:
            raise ValueError("Total pot must be positive when bet_to_call is > 0.")

        return bet_to_call / denominator

    @staticmethod
    def calculate_break_even_equity(pot_odds: float) -> float:
        """Return the break-even equity, which equals the pot odds."""
        if pot_odds < 0:
            raise ValueError("Pot odds cannot be negative.")
        return pot_odds

    def calculate_implied_odds(self, game_state: GameState, future_bets: float = 0.0) -> float:
        """Return implied odds ``bet_to_call / (pot_size + future_bets + bet_to_call)``."""
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState instance.")
        if future_bets < 0:
            raise ValueError("future_bets cannot be negative.")

        bet_to_call = max(game_state.bet_to_call, 0.0)
        if bet_to_call == 0:
            return 0.0

        pot_size = max(game_state.pot_size, 0.0)
        denominator = pot_size + future_bets + bet_to_call
        if denominator <= 0:
            raise ValueError("Total pot plus future bets must be positive.")

        return bet_to_call / denominator

    @staticmethod
    def calculate_ev(win_probability: float, pot_size: float, bet_amount: float) -> float:
        r"""Return expected value using ``(W% × Pot) - ((1 - W%) × Bet)``."""
        if not 0 <= win_probability <= 1:
            raise ValueError("win_probability must be between 0 and 1.")
        if pot_size < 0:
            raise ValueError("pot_size cannot be negative.")
        if bet_amount < 0:
            raise ValueError("bet_amount cannot be negative.")

        win_ev = win_probability * pot_size
        lose_ev = (1 - win_probability) * bet_amount
        return win_ev - lose_ev

    @staticmethod
    def outs_to_percentage(outs: int, cards_to_come: int = 1) -> float:
        """Convert outs to probability using the rule of 2 and 4."""
        if outs < 0:
            raise ValueError("outs cannot be negative.")
        if cards_to_come not in (1, 2):
            raise ValueError("cards_to_come must be 1 or 2 for the rule of 2 and 4.")

        multiplier = 0.02 if cards_to_come == 1 else 0.04
        return outs * multiplier
