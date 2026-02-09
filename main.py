#!/usr/bin/env python3
import sys
from carta_app import CartaApp
from PyQt5.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    # Tema oscuro
    dark_stylesheet = """
        QWidget {
            background-color: #232629;
            color: #F8F8F2;
        }
        QTabWidget::pane {
            border: 1px solid #44475a;
        }
        QTabBar::tab {
            background: #282a36;
            color: #f8f8f2;
            border: 1px solid #44475a;
            padding: 8px;
        }
        QTabBar::tab:selected {
            background: #44475a;
        }
        QLabel {
            color: #f8f8f2;
        }
    """
    app.setStyleSheet(dark_stylesheet)
    window = CartaApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
