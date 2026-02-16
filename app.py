"""LoL Companion — Entry point."""

import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt
from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RiftRetreat")
    app.setOrganizationName("Treatey")
    app.setApplicationVersion("1.1.0")

    # Create splash screen
    splash = QSplashScreen()
    splash.setFixedSize(400, 200)
    splash.setStyleSheet("background-color: #0a1428; border: 2px solid #c89b3c;")

    # Add loading text
    label = QLabel("Loading RiftRetreat...", splash)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("color: #c89b3c; font-size: 18px; font-weight: bold;")
    label.setGeometry(0, 80, 400, 40)

    splash.show()
    app.processEvents()

    # Initialize main window (heavy operation)
    window = MainWindow()

    # Close splash and show main window
    splash.close()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
