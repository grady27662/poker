"""Main window implementation for the Poker Coach GUI."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.engine.decision_engine import DecisionEngine
from src.models.action import ActionType
from src.models.card import Card
from src.models.game_state import GameState, Position, Street

__all__ = ["PokerCoachWindow", "launch_main_window"]


@dataclass(frozen=True)
class _CardWidgets:
    """Small container storing widgets for a single card selection."""

    container: QWidget
    rank_combo: QComboBox
    suit_combo: QComboBox


class PokerCoachWindow(QMainWindow):
    """Janela principal do aplicativo Poker Coach."""

    RANK_OPTIONS: Sequence[str] = ("A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2")
    SUIT_OPTIONS: Sequence[str] = ("♠", "♥", "♦", "♣")
    STREET_LABELS: Dict[str, Street] = {
        "Pre-Flop": Street.PREFLOP,
        "Flop": Street.FLOP,
        "Turn": Street.TURN,
        "River": Street.RIVER,
    }
    POSITION_LABELS: Dict[str, Position] = {
        "UTG": Position.UTG,
        "MP": Position.MP,
        "CO": Position.CO,
        "BTN": Position.BTN,
        "SB": Position.SB,
        "BB": Position.BB,
    }

    ACTION_COLORS: Dict[ActionType, str] = {
        ActionType.FOLD: "#e74c3c",
        ActionType.CHECK: "#f1c40f",
        ActionType.CALL: "#27ae60",
        ActionType.BET: "#27ae60",
        ActionType.RAISE: "#27ae60",
        ActionType.ALL_IN: "#8e44ad",
    }

    def __init__(self) -> None:
        super().__init__()
        self.game_state: GameState = GameState()
        self.decision_engine = DecisionEngine()

        # UI component references
        self.card1_rank: QComboBox
        self.card1_suit: QComboBox
        self.card2_rank: QComboBox
        self.card2_suit: QComboBox
        self.street_combo: QComboBox
        self.board_group: QGroupBox
        self.board_container: QWidget
        self.board_cards: List[_CardWidgets] = []
        self.position_combo: QComboBox
        self.pot_spin: QSpinBox
        self.bet_spin: QSpinBox
        self.stack_spin: QSpinBox
        self.opponents_spin: QSpinBox
        self.recommendation_label: QLabel
        self.analyze_button: QPushButton

        self.init_ui()

    # ------------------------------------------------------------------ UI BUILDERS
    def init_ui(self) -> None:
        """Configura a interface da janela."""
        self.setWindowTitle("Poker Coach - Assistente Inteligente")
        self.resize(900, 720)
        self.move(120, 60)

        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(18, 18, 18, 18)

        main_layout.addWidget(self._build_hole_cards_section())
        main_layout.addWidget(self._build_board_section())
        main_layout.addWidget(self._build_game_info_section())
        main_layout.addWidget(self._build_recommendation_section())
        main_layout.addWidget(self._build_action_button())

        self.setCentralWidget(central_widget)
        self._apply_styles()

        # Atualiza visibilidade inicial do board
        self.on_street_changed(self.street_combo.currentText())

    def _build_hole_cards_section(self) -> QGroupBox:
        group = QGroupBox("🃏 Suas Cartas", self)
        layout = QHBoxLayout(group)
        layout.setSpacing(12)

        self.card1_rank = QComboBox(group)
        self.card1_rank.addItems(self.RANK_OPTIONS)
        self.card1_suit = QComboBox(group)
        self.card1_suit.addItems(self.SUIT_OPTIONS)

        self.card2_rank = QComboBox(group)
        self.card2_rank.addItems(self.RANK_OPTIONS)
        self.card2_suit = QComboBox(group)
        self.card2_suit.addItems(self.SUIT_OPTIONS)

        layout.addWidget(QLabel("Carta 1:", group))
        layout.addWidget(self.card1_rank)
        layout.addWidget(self.card1_suit)
        layout.addSpacing(24)
        layout.addWidget(QLabel("Carta 2:", group))
        layout.addWidget(self.card2_rank)
        layout.addWidget(self.card2_suit)
        layout.addStretch()

        return group

    def _build_board_section(self) -> QGroupBox:
        self.board_group = QGroupBox("🎴 Mesa (Board)", self)
        outer_layout = QVBoxLayout(self.board_group)
        outer_layout.setSpacing(12)

        self.street_combo = QComboBox(self.board_group)
        self.street_combo.addItems(self.STREET_LABELS.keys())
        self.street_combo.currentTextChanged.connect(self.on_street_changed)
        outer_layout.addWidget(QLabel("Street atual:", self.board_group))
        outer_layout.addWidget(self.street_combo)

        self.board_container = QWidget(self.board_group)
        board_layout = QHBoxLayout(self.board_container)
        board_layout.setSpacing(10)

        for index in range(5):
            card_widget = QWidget(self.board_container)
            card_layout = QVBoxLayout(card_widget)
            card_layout.setSpacing(6)
            card_layout.setContentsMargins(0, 0, 0, 0)

            rank_combo = QComboBox(card_widget)
            rank_combo.addItems(("", *self.RANK_OPTIONS))
            suit_combo = QComboBox(card_widget)
            suit_combo.addItems(("", *self.SUIT_OPTIONS))

            card_label = QLabel(f"Carta {index + 1}:", card_widget)
            card_layout.addWidget(card_label)
            card_layout.addWidget(rank_combo)
            card_layout.addWidget(suit_combo)

            board_layout.addWidget(card_widget)
            self.board_cards.append(_CardWidgets(card_widget, rank_combo, suit_combo))

        outer_layout.addWidget(self.board_container)
        return self.board_group

    def _build_game_info_section(self) -> QGroupBox:
        group = QGroupBox("ℹ️ Informações do Jogo", self)
        layout = QVBoxLayout(group)
        layout.setSpacing(12)

        self.position_combo = QComboBox(group)
        self.position_combo.addItems(self.POSITION_LABELS.keys())
        self.position_combo.setCurrentText("BTN")

        self.pot_spin = QSpinBox(group)
        self.pot_spin.setRange(0, 100_000)
        self.pot_spin.setValue(100)
        self.pot_spin.setSuffix(" fichas")

        self.bet_spin = QSpinBox(group)
        self.bet_spin.setRange(0, 100_000)
        self.bet_spin.setSuffix(" fichas")

        self.stack_spin = QSpinBox(group)
        self.stack_spin.setRange(0, 100_000)
        self.stack_spin.setValue(1000)
        self.stack_spin.setSuffix(" fichas")

        self.opponents_spin = QSpinBox(group)
        self.opponents_spin.setRange(1, 9)
        self.opponents_spin.setValue(2)

        layout.addLayout(self._horizontal_row("Posição:", self.position_combo))
        layout.addLayout(self._horizontal_row("Tamanho do Pot:", self.pot_spin))
        layout.addLayout(self._horizontal_row("Aposta para Call:", self.bet_spin))
        layout.addLayout(self._horizontal_row("Seu Stack:", self.stack_spin))
        layout.addLayout(self._horizontal_row("Oponentes Ativos:", self.opponents_spin))

        return group

    def _build_recommendation_section(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.recommendation_label = QLabel("⏳ Aguardando informações...", container)
        self.recommendation_label.setObjectName("recommendationLabel")
        self.recommendation_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.recommendation_label.setMinimumHeight(160)
        self.recommendation_label.setWordWrap(True)

        layout.addWidget(self.recommendation_label)
        return container

    def _build_action_button(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.analyze_button = QPushButton("🎯 ANALISAR E RECOMENDAR", container)
        self.analyze_button.setObjectName("analyzeButton")
        self.analyze_button.clicked.connect(self.analyze_hand)
        layout.addWidget(self.analyze_button, alignment=Qt.AlignmentFlag.AlignCenter)
        return container

    def _horizontal_row(self, label_text: str, widget: QWidget) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)
        label = QLabel(label_text, self)
        layout.addWidget(label, stretch=1)
        layout.addWidget(widget, stretch=2)
        return layout

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            * {
                font-family: 'Arial', sans-serif;
                font-size: 13px;
            }
            QMainWindow {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QGroupBox {
                background-color: #ecf0f1;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 12px;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
                font-weight: bold;
            }
            QLabel {
                color: #2c3e50;
            }
            QComboBox, QSpinBox {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 4px;
                min-width: 80px;
                color: #2c3e50;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QPushButton#analyzeButton {
                background-color: #27ae60;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
                padding: 14px 22px;
                border-radius: 10px;
            }
            QPushButton#analyzeButton:hover {
                background-color: #229954;
            }
            QLabel#recommendationLabel {
                background-color: #34495e;
                color: #ffffff;
                border-radius: 12px;
                padding: 20px;
                font-size: 14px;
            }
            """
        )

    # ------------------------------------------------------------------ EVENT HANDLERS
    def on_street_changed(self, street_text: str) -> None:
        """Altera visibilidade das cartas do board conforme a street."""
        required_cards = {
            "Pre-Flop": 0,
            "Flop": 3,
            "Turn": 4,
            "River": 5,
        }.get(street_text, 0)

        self.board_container.setVisible(required_cards > 0)
        for index, card_widgets in enumerate(self.board_cards):
            card_widgets.container.setVisible(index < required_cards)

    # ------------------------------------------------------------------ GAME STATE
    def update_game_state(self) -> None:
        """Atualiza o estado do jogo com os dados da interface."""
        hole_cards = [
            Card.from_string(self.card1_rank.currentText() + self.card1_suit.currentText()),
            Card.from_string(self.card2_rank.currentText() + self.card2_suit.currentText()),
        ]

        board_cards: List[Card] = []
        for card_widgets in self.board_cards:
            rank_text = card_widgets.rank_combo.currentText()
            suit_text = card_widgets.suit_combo.currentText()
            if rank_text and suit_text:
                board_cards.append(Card.from_string(rank_text + suit_text))

        street = self.STREET_LABELS[self.street_combo.currentText()]
        position = self.POSITION_LABELS[self.position_combo.currentText()]
        pot_size = float(self.pot_spin.value())
        bet_to_call = float(self.bet_spin.value())
        stack = float(self.stack_spin.value())
        active_opponents = int(self.opponents_spin.value())

        opponent_stacks = [stack] * active_opponents

        self.game_state = GameState(
            hole_cards=hole_cards,
            board=board_cards,
            street=street,
            pot_size=pot_size,
            bet_to_call=bet_to_call,
            your_stack=stack,
            opponent_stacks=opponent_stacks,
            your_position=position,
            num_opponents=max(active_opponents, 1),
            active_opponents=active_opponents,
        )

    # ------------------------------------------------------------------ ANALYSIS
    def analyze_hand(self) -> None:
        """Executa a análise de mão usando o motor de decisão."""
        self.analyze_button.setEnabled(False)
        self.recommendation_label.setText("⏳ Calculando recomendação...")

        try:
            self.update_game_state()
            action, amount, reasoning = self.decision_engine.recommend_action(self.game_state)
            self._display_recommendation(action, amount, reasoning)
        except NotImplementedError:
            self._display_error("Motor de decisão ainda não implementado. Aguarde próximas versões.")
        except Exception as exc:  # pylint: disable=broad-except
            self._display_error(f"Erro ao analisar mão: {exc}")
        finally:
            self.analyze_button.setEnabled(True)

    def _display_recommendation(self, action: ActionType, amount: float, reasoning: Sequence[str]) -> None:
        color = self.ACTION_COLORS.get(action, "#ffffff")
        action_text = action.value.upper().replace("_", " ")
        amount_html = f"<p><b>Valor sugerido:</b> {amount:.0f} fichas</p>" if amount > 0 else ""
        reasoning_items = "".join(f"<li>{step}</li>" for step in reasoning)
        reasoning_html = f"<ul>{reasoning_items}</ul>" if reasoning_items else "<p>Sem justificativas detalhadas.</p>"

        html = (
            f"<h2 style='color:{color};'>Recomendação: {action_text}</h2>"
            f"{amount_html}"
            f"<h3>Raciocínio:</h3>"
            f"{reasoning_html}"
        )

        self.recommendation_label.setText(html)

    def _display_error(self, message: str) -> None:
        error_html = (
            "<h2 style='color:#e74c3c;'>❌ Erro na análise</h2>"
            f"<p>{message}</p>"
        )
        self.recommendation_label.setText(error_html)


def launch_main_window() -> None:
    """Inicia a aplicação Qt exibindo a janela principal."""
    app = QApplication(sys.argv)
    window = PokerCoachWindow()
    window.show()
    app.exec()
