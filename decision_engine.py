"""Decision-making engine for Poker Coach.

The goal is to blend pre-flop range logic, odds calculations and Monte Carlo
simulations to produce an actionable recommendation (ação + tamanho + raciocínio).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from src.engine.hand_evaluator import HandEvaluator
from src.engine.monte_carlo import MonteCarloSimulator
from src.engine.odds_calculator import OddsCalculator
from src.models.action import ActionType
from src.models.game_state import GameState, Street
from src.strategy.ranges import PreflopRanges

__all__ = ["DecisionEngine", "DecisionResult"]


@dataclass(frozen=True)
class DecisionResult:
    """Container for decision output."""

    action: ActionType
    amount: float
    reasoning: Sequence[str]


class DecisionEngine:
    """High-level poker decision maker integrating all calculators."""

    PREMIUM_HANDS = {"AA", "KK", "QQ", "AKS", "AKO"}
    STRONG_HANDS = {"JJ", "TT", "99", "AQS", "AJS", "AQO", "KQS"}
    SPECULATIVE_HANDS = {
        "ATs".upper(),
        "KJs".upper(),
        "QJs".upper(),
        "JTs".upper(),
        "T9s".upper(),
        "98s".upper(),
        "87s".upper(),
        "A5s".upper(),
        "A4s".upper(),
        "A3s".upper(),
        "A2s".upper(),
        "KTs".upper(),
        "QTs".upper(),
    }

    def __init__(self, num_simulations: int = 5_000) -> None:
        self.hand_evaluator = HandEvaluator()
        self.odds_calculator = OddsCalculator()
        self.monte_carlo = MonteCarloSimulator(num_simulations=num_simulations)

    # ------------------------------------------------------------------ PUBLIC API
    def recommend_action(self, game_state: GameState) -> Tuple[ActionType, float, List[str]]:
        """Return the best action tuple (action, amount, reasoning)."""
        if len(game_state.hole_cards) != 2:
            raise ValueError("É necessário informar exatamente duas cartas na mão.")

        if game_state.street == Street.PREFLOP:
            result = self._recommend_preflop(game_state)
        else:
            result = self._recommend_postflop(game_state)

        return result.action, result.amount, list(result.reasoning)

    # ------------------------------------------------------------------ PREFLOP
    def _recommend_preflop(self, game_state: GameState) -> DecisionResult:
        reasoning: List[str] = []
        hero_cards = [str(card) for card in game_state.hole_cards]
        combo = PreflopRanges.normalize_hand(*hero_cards)
        reasoning.append(f"Mão normalizada: {combo}")
        reasoning.append(f"Posição: {game_state.your_position.value}")

        bet_to_call = game_state.bet_to_call
        pot_odds = self.odds_calculator.calculate_pot_odds(game_state) if bet_to_call > 0 else 0.0
        if bet_to_call > 0:
            reasoning.append(f"Pot odds: {self._format_percentage(pot_odds)}")

        if bet_to_call == 0:
            if PreflopRanges.should_open(combo, game_state.your_position):
                reasoning.append("Mão está no range de abertura para a posição.")
                amount = self._suggest_open_raise(game_state)
                return DecisionResult(ActionType.RAISE, amount, reasoning)

            reasoning.append("Mão fora do range de abertura → Fold.")
            return DecisionResult(ActionType.FOLD, 0.0, reasoning)

        normalized_combo = combo.upper()
        if normalized_combo in self.PREMIUM_HANDS:
            reasoning.append("Mão premium → aproveitar valor com 3-bet.")
            amount = self._suggest_3bet_size(game_state)
            return self._short_stack_adjustment(game_state, ActionType.RAISE, amount, reasoning)

        equity = self._estimate_equity(game_state)
        reasoning.append(f"Equity estimada vs range adversário: {self._format_percentage(equity)}")

        multiway_adjust = self._multiway_adjustment(game_state.active_opponents)
        required_equity = pot_odds + multiway_adjust
        reasoning.append(f"Equity mínima considerando pot odds e multiway: {self._format_percentage(required_equity)}")

        if normalized_combo in self.STRONG_HANDS:
            if equity >= required_equity + 0.1:
                reasoning.append("Equity bem acima do necessário → agressão.")
                amount = self._suggest_3bet_size(game_state)
                return self._short_stack_adjustment(game_state, ActionType.RAISE, amount, reasoning)
            if equity >= required_equity:
                reasoning.append("Equity suficiente para pagar a aposta.")
                amount = min(bet_to_call, game_state.your_stack)
                return self._short_stack_adjustment(game_state, ActionType.CALL, amount, reasoning)

        if normalized_combo in self.SPECULATIVE_HANDS:
            implied_odds = self.odds_calculator.calculate_implied_odds(game_state, future_bets=game_state.pot_size * 0.5)
            reasoning.append(f"Implied odds aproximadas: {self._format_percentage(implied_odds)}")
            if equity >= implied_odds:
                reasoning.append("Equity cobre as implied odds → call especulativo.")
                amount = min(bet_to_call, game_state.your_stack)
                return self._short_stack_adjustment(game_state, ActionType.CALL, amount, reasoning)

        reasoning.append("Equity insuficiente → Fold.")
        return DecisionResult(ActionType.FOLD, 0.0, reasoning)

    # ------------------------------------------------------------------ POSTFLOP
    def _recommend_postflop(self, game_state: GameState) -> DecisionResult:
        reasoning: List[str] = []
        if len(game_state.board) < 3 and game_state.street != Street.PREFLOP:
            reasoning.append("⚠️ Board incompleto - resultados podem ser imprecisos.")

        equity = self._estimate_equity(game_state)
        reasoning.append(f"Equity estimada: {self._format_percentage(equity)}")

        pot_odds = self.odds_calculator.calculate_pot_odds(game_state) if game_state.bet_to_call > 0 else 0.0
        reasoning.append(f"Pot odds atuais: {self._format_percentage(pot_odds)}")

        multiway_adjust = self._multiway_adjustment(game_state.active_opponents)
        reasoning.append(f"Ajuste multiway: +{self._format_percentage(multiway_adjust)} de equity necessária.")

        if game_state.bet_to_call == 0:
            if equity >= 0.65 + multiway_adjust:
                reasoning.append("Equity muito alta → apostar por valor.")
                amount = self._suggest_value_bet(game_state)
                return self._short_stack_adjustment(game_state, ActionType.BET, amount, reasoning)
            if equity >= 0.45 + multiway_adjust:
                reasoning.append("Equity média → linha passiva ou aposta pequena.")
                amount = self._suggest_small_bet(game_state)
                if amount > 0:
                    return self._short_stack_adjustment(game_state, ActionType.BET, amount, reasoning)
                return DecisionResult(ActionType.CHECK, 0.0, reasoning)

            reasoning.append("Equity baixa → manter controle do pote.")
            return DecisionResult(ActionType.CHECK, 0.0, reasoning)

        required_equity = pot_odds * 1.15 + multiway_adjust
        reasoning.append(f"Equity mínima para continuação: {self._format_percentage(required_equity)}")

        if equity >= required_equity:
            if equity >= 0.70 + multiway_adjust:
                reasoning.append("Equity dominante → raise por valor.")
                amount = self._suggest_raise_size(game_state)
                return self._short_stack_adjustment(game_state, ActionType.RAISE, amount, reasoning)

            reasoning.append("Equity suficiente → call lucrativo.")
            amount = min(game_state.bet_to_call, game_state.your_stack)
            return self._short_stack_adjustment(game_state, ActionType.CALL, amount, reasoning)

        reasoning.append("Equity abaixo da exigência → Fold recomendado.")
        return DecisionResult(ActionType.FOLD, 0.0, reasoning)

    # ------------------------------------------------------------------ HELPERS
    def _estimate_equity(self, game_state: GameState) -> float:
        try:
            return self.monte_carlo.simulate_equity(
                hero_cards=game_state.hole_cards,
                board=game_state.board,
                num_opponents=max(1, game_state.active_opponents),
            )
        except ValueError as exc:
            # Falha na simulação (cartas insuficientes, etc.) → conservar valor padrão neutro.
            return 0.0

    @staticmethod
    def _format_percentage(value: float) -> str:
        return f"{value * 100:.1f}%"

    @staticmethod
    def _multiway_adjustment(opponents: int) -> float:
        extras = max(0, opponents - 1)
        return extras * 0.05

    def _suggest_open_raise(self, game_state: GameState) -> float:
        big_blind = self._infer_big_blind(game_state)
        amount = 2.7 * big_blind
        return min(amount, game_state.your_stack)

    def _suggest_3bet_size(self, game_state: GameState) -> float:
        base = game_state.bet_to_call * 3 if game_state.bet_to_call > 0 else self._infer_big_blind(game_state) * 3
        return min(base, game_state.your_stack)

    def _suggest_value_bet(self, game_state: GameState) -> float:
        amount = max(game_state.pot_size * 0.6, game_state.pot_size * 0.5)
        return min(amount, game_state.your_stack)

    def _suggest_small_bet(self, game_state: GameState) -> float:
        amount = game_state.pot_size * 0.4
        return min(amount, game_state.your_stack) if amount > 0 else 0.0

    def _suggest_raise_size(self, game_state: GameState) -> float:
        amount = max(game_state.bet_to_call * 2.5, game_state.pot_size * 0.8)
        return min(amount, game_state.your_stack)

    def _infer_big_blind(self, game_state: GameState) -> float:
        if game_state.pot_size > 0:
            return max(1.0, game_state.pot_size / 1.5)
        return 10.0

    def _short_stack_adjustment(
        self,
        game_state: GameState,
        action: ActionType,
        amount: float,
        reasoning: List[str],
    ) -> DecisionResult:
        effective_stack = game_state.effective_stack
        if effective_stack <= max(game_state.pot_size * 1.5, game_state.bet_to_call):
            reasoning.append("Stack efetivo curto → considerar all-in simplificado.")
            return DecisionResult(ActionType.ALL_IN, effective_stack, reasoning)

        capped_amount = min(amount, game_state.your_stack)
        return DecisionResult(action, capped_amount, reasoning)
