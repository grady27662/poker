"""Poker Coach application entry point.

Execute with:
    python -m src.main
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from src.gui.main_window import PokerCoachWindow


def main() -> None:
    """Inicializa QApplication e exibe a janela principal do Poker Coach."""
    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        * {
            font-family: 'Arial', sans-serif;
        }
        QComboBox, QSpinBox {
            padding: 4px;
            border-radius: 6px;
        }
        """
    )

    window = PokerCoachWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
