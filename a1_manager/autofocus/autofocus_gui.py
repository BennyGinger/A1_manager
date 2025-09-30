"""GUI utilities for autofocus operations using PyQt6."""

import sys
import numpy as np
import logging

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QFont

logger = logging.getLogger(__name__)


class AutofocusResult:
    """Result from autofocus GUI prompt."""
    CONTINUE = "continue"
    RESTART = "restart"
    QUIT = "quit"


class AutofocusWidget(QWidget):
    """Widget for autofocus image review (embeddable)."""
    result_signal = pyqtSignal(str)  # Emits the result: CONTINUE, RESTART, or QUIT

    def __init__(self, image: np.ndarray, title: str = "Current Focus", parent=None):
        super().__init__(parent)
        self.image = image
        self.window_title = title
        self.result = None
        self.original_pixmap = None  # Store original pixmap for resizing
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumSize(600, 500)
        self.resize(800, 650)
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel(self.window_title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Instructions
        instruction_text = "Review focus quality and choose an action:"
        instruction_label = QLabel(instruction_text)
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)

        # Image display
        pixmap = self._convert_to_pixmap(self.image)
        self.original_pixmap = pixmap
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.image_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.quit_btn = QPushButton("❌ Quit")
        self.quit_btn.setFixedSize(120, 40)
        self.quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc3333;
            }
        """)
        self.quit_btn.clicked.connect(lambda: self._on_button_click(AutofocusResult.QUIT))

        self.restart_btn = QPushButton("🔄 Restart")
        self.restart_btn.setFixedSize(120, 40)
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffaa00;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dd8800;
            }
        """)
        self.restart_btn.clicked.connect(lambda: self._on_button_click(AutofocusResult.RESTART))

        self.continue_btn = QPushButton("✅ Continue")
        self.continue_btn.setFixedSize(120, 40)
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #44aa44;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #338833;
            }
        """)
        self.continue_btn.clicked.connect(lambda: self._on_button_click(AutofocusResult.CONTINUE))
        self.continue_btn.setDefault(True)

        button_layout.addStretch()
        button_layout.addWidget(self.quit_btn)
        button_layout.addWidget(self.restart_btn)
        button_layout.addWidget(self.continue_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        self.continue_btn.setFocus()

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if self.original_pixmap and hasattr(self, 'image_label'):
            available_size = self.image_label.size()
            scaled_pixmap = self.original_pixmap.scaled(
                available_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def showEvent(self, a0):
        super().showEvent(a0)
        QTimer.singleShot(50, self._update_image_scale)

    def _update_image_scale(self):
        if self.original_pixmap and hasattr(self, 'image_label'):
            available_size = self.image_label.size()
            scaled_pixmap = self.original_pixmap.scaled(
                available_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def _convert_to_pixmap(self, image: np.ndarray) -> QPixmap:
        # ...same as before...
        if image.dtype != np.uint8:
            vmin, vmax = np.percentile(image, [2, 98])
            image_norm = np.clip((image - vmin) / (vmax - vmin) * 255, 0, 255).astype(np.uint8)
        else:
            vmin, vmax = np.percentile(image, [1, 99])
            if vmax > vmin:
                image_norm = np.clip((image.astype(float) - vmin) / (vmax - vmin) * 255, 0, 255).astype(np.uint8)
            else:
                image_norm = image
        if len(image_norm.shape) == 2:
            height, width = image_norm.shape
            bytes_per_line = width
            qt_format = QImage.Format.Format_Grayscale8
        else:
            height, width, channels = image_norm.shape
            bytes_per_line = channels * width
            if channels == 3:
                qt_format = QImage.Format.Format_RGB888
            elif channels == 4:
                qt_format = QImage.Format.Format_RGBA8888
            else:
                raise ValueError(f"Unsupported number of channels: {channels}")
        qt_image = QImage(image_norm.data, width, height, bytes_per_line, qt_format)
        pixmap = QPixmap.fromImage(qt_image)
        max_width, max_height = 730, 500
        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        return pixmap

    def _on_button_click(self, result: str):
        self.result = result
        self.result_signal.emit(result)
        self.hide()

    def keyPressEvent(self, a0):
        if a0 is not None:
            if a0.key() == Qt.Key.Key_Return or a0.key() == Qt.Key.Key_Enter:
                self._on_button_click(AutofocusResult.CONTINUE)
            elif a0.key() == Qt.Key.Key_Escape:
                self._on_button_click(AutofocusResult.QUIT)
            elif a0.key() == Qt.Key.Key_R:
                self._on_button_click(AutofocusResult.RESTART)
            else:
                super().keyPressEvent(a0)
        else:
            super().keyPressEvent(a0)

# --- Keep AutofocusWindow for backward compatibility (modal window) ---
class AutofocusWindow(QMainWindow):
    """Main window for autofocus image review (standalone window)."""
    def __init__(self, image: np.ndarray, title: str = "Current Focus"):
        super().__init__()
        self.widget = AutofocusWidget(image, title)
        self.setCentralWidget(self.widget)
        self.setWindowTitle("Focus Review")
        self.setMinimumSize(600, 500)
        self.resize(800, 650)
        self.result = None

    def keyPressEvent(self, a0):
        self.widget.keyPressEvent(a0)
        self.result = self.widget.result
        if self.result is not None:
            self.close()

    def closeEvent(self, a0):
        if self.result is None:
            self.result = self.widget.result or AutofocusResult.QUIT
        if a0 is not None:
            a0.accept()


def prompt_autofocus_gui(image: np.ndarray, title: str = "Current Focus") -> str:
    """
    Show autofocus GUI and return user choice.
    
    Args:
        image (np.ndarray): The image to display for focus evaluation
        title (str): Title for the window
        
    Returns:
        str: One of AutofocusResult.CONTINUE, AutofocusResult.RESTART, or AutofocusResult.QUIT
    """
    try:
        # Ensure we have a QApplication
        app = QApplication.instance()
        
        if app is None:
            app = QApplication(sys.argv)
            logger.debug("Created new QApplication")
        else:
            logger.debug("Using existing QApplication")
        
        # Create the window
        window = AutofocusWindow(image, title)
        
        # Show the window and ensure it's properly displayed
        window.show()
        window.raise_()
        window.activateWindow()
        
        # Process events to ensure window is shown
        app.processEvents()
        
        # Simple polling loop - avoid exec() which can interfere with existing event loops
        import time
        
        while window.isVisible() and window.result is None:
            app.processEvents()
            time.sleep(0.01)  # Small delay to prevent busy waiting
        
        # Get the result
        final_result = window.result or AutofocusResult.QUIT
        
        # Clean up the window
        window.close()
        window.deleteLater()
        app.processEvents()
        
        logger.debug(f"GUI result: {final_result}")
        return final_result
        
    except Exception as e:
        logger.error(f"PyQt6 GUI failed: {e}", exc_info=True)
        # Fallback to terminal prompt
        return _fallback_terminal_prompt()


def _fallback_terminal_prompt() -> str:
    """Fallback to terminal prompt if GUI fails."""
    print("\n" + "="*60)
    print("🔍 AUTOFOCUS REVIEW")
    print("="*60)
    print("Please review the focus quality.")
    print("Options:")
    print("  - Press Enter to CONTINUE")
    print("  - Type 'r' to RESTART autofocus")
    print("  - Type 'q' to QUIT")
    print("="*60)
    
    while True:
        resp = input("Your choice: ").strip().lower()
        if resp == '' or resp == 'c':
            return AutofocusResult.CONTINUE
        elif resp == 'r':
            return AutofocusResult.RESTART
        elif resp == 'q':
            return AutofocusResult.QUIT
        else:
            print("Invalid input. Please press Enter, type 'r', or type 'q'.")
