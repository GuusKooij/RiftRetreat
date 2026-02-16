"""Loading dialog to show progress and prevent user interaction."""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LoadingDialog(QDialog):
    """Modal dialog that shows loading progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading RiftRetreat")
        self.setModal(True)  # Block interaction with parent
        self.setFixedSize(500, 200)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        # Dark theme styling
        self.setStyleSheet("""
            QDialog {
                background-color: #0A1428;
                border: 2px solid #C89B3C;
            }
            QLabel {
                color: #F0E6D2;
            }
            QProgressBar {
                border: 2px solid #1E2328;
                border-radius: 5px;
                text-align: center;
                background-color: #1E2328;
                color: #F0E6D2;
            }
            QProgressBar::chunk {
                background-color: #C89B3C;
                border-radius: 3px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        self.title_label = QLabel("Loading Data...")
        self.title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #C89B3C;")
        layout.addWidget(self.title_label)

        # Status message
        self.status_label = QLabel("Please wait...")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Info message
        self.info_label = QLabel("This may take some time.\nPlease do not close the application.")
        self.info_label.setFont(QFont("Arial", 10))
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #A09B8C;")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def update_progress(self, current: int, total: int, message: str):
        """Update the progress bar and message."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)

        self.status_label.setText(message)

        # Force update
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
