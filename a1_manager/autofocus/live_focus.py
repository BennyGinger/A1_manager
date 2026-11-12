from __future__ import annotations

import logging
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PyQt6.QtCore import QEventLoop, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QImage, QPixmap, QResizeEvent
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from a1_manager.a1manager import A1Manager
from a1_manager.autofocus.display_controls import DisplayControls
from a1_manager.utils.image_display import apply_display_lut

logger = logging.getLogger(__name__)


class LiveFocusWidget(QWidget):
    """
    Stream the camera while the user adjusts focus with the microscope controls.
    """

    result_signal = pyqtSignal(str)

    def __init__(self, a1_manager: A1Manager) -> None:
        """
        Build the review and start acquisition using the current optical settings.
        """
        super().__init__()
        self.core: Any = a1_manager.core
        self.result: str | None = None
        self._stopped = False
        self._started_sequence = False
        self._frame: NDArray[np.uint8 | np.uint16] | None = None
        self._pixmap: QPixmap | None = None
        self._auto_shutter = self.core.get_auto_shutter()
        self._shutter_open = self.core.get_shutter_open()
        self._light_path = (self.core.get_property('LappMainBranch1', 'State')
                            if a1_manager.dmd is not None else None)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self._setup_ui()
        self._start_live_view()

    def _setup_ui(self) -> None:
        """
        Build the live image display and Continue control.
        """
        self.setWindowTitle("Focus adjustment")
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Adjust focus using the microscope controls, then press Continue."))
        self.image_label = QLabel("Waiting for camera frames…")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 350)
        image_row = QHBoxLayout()
        layout.addLayout(image_row, 1)
        self.display_controls = DisplayControls()
        self.display_controls.setMaximumWidth(280)
        self.display_controls.setEnabled(False)
        self.display_controls.changed.connect(self._render_frame)
        self.display_controls.auto_scale_requested.connect(self._auto_scale)
        image_row.addWidget(self.display_controls, 0, Qt.AlignmentFlag.AlignTop)
        image_row.addWidget(self.image_label, 1)
        self.continue_button = QPushButton("Continue")
        self.continue_button.setMinimumSize(160, 56)
        self.continue_button.setStyleSheet(
            "QPushButton { background: #24883a; color: white; font-weight: bold; "
            "font-size: 12pt; padding: 14px 24px; }"
            "QPushButton:hover { background: #1c7130; }"
            "QPushButton:disabled { background: #9aaf9d; color: #e9e9e9; }"
        )
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(lambda: self._finish("continue"))
        image_row.addWidget(self.continue_button, 0, Qt.AlignmentFlag.AlignBottom)

    def _start_live_view(self) -> None:
        """
        Start an owned sequence with continuous illumination, or borrow the running one.
        """
        try:
            if not self.core.is_sequence_running():
                self._started_sequence = True
                self.core.clear_circular_buffer()
                # Use the lamp's direct path so a timed DMD exposure cannot darken the preview.
                if self._light_path is not None:
                    self.core.set_property('LappMainBranch1', 'State', 1)
                self.core.set_auto_shutter(False)
                self.core.set_shutter_open(True)
                self.core.start_continuous_sequence_acquisition(0)
            self.timer.start(33)
        except Exception:
            self.stop_live_view()
            raise

    def _update_frame(self) -> None:
        """
        Display the newest frame and quit if acquisition fails.
        """
        try:
            if not self.core.is_sequence_running():
                raise RuntimeError("Live camera acquisition stopped unexpectedly")
            if self.core.get_remaining_image_count() == 0:
                return
            tagged_image = self.core.get_last_tagged_image()
            pixel_type = tagged_image.tags['PixelType']
            if pixel_type not in ('GRAY8', 'GRAY16'):
                raise ValueError(f"Unsupported live camera pixel type: {pixel_type}")
            first_frame = self._frame is None
            dtype = np.uint8 if pixel_type == 'GRAY8' else np.uint16
            self._frame = np.asarray(tagged_image.pix).astype(dtype).reshape(tagged_image.tags['Height'],
                                                                            tagged_image.tags['Width'],
                                                                            )
            if first_frame:
                self.display_controls.setEnabled(True)
                self._auto_scale()
            else:
                self._render_frame()
            self.continue_button.setEnabled(True)
        except Exception:
            logger.exception("Live focus preview failed")
            self._finish("quit")

    def _auto_scale(self) -> None:
        """
        Fit the LUT to the current frame's 0.1 and 99.9 percentiles, as in tuning.
        """
        if self._frame is None:
            return
        full_range = int(np.iinfo(self._frame.dtype).max)
        lower, upper = np.percentile(self._frame, [0.1, 99.9])
        minimum = min(int(np.floor(lower)), full_range - 1)
        maximum = min(max(int(np.ceil(upper)), minimum + 1), full_range)
        self.display_controls.set_levels(minimum, maximum, full_range)

    def _render_frame(self) -> None:
        """
        Apply display settings to the latest raw frame without changing camera data.
        """
        if self._frame is None:
            return
        controls = self.display_controls
        normalized = apply_display_lut(self._frame, controls.min_slider.value(),
                                       controls.max_slider.value(),
                                       controls.brightness_slider.value(),
                                       controls.contrast_slider.value(),
                                       )
        pixels = (normalized * 255).astype(np.uint8)
        height, width = pixels.shape
        image = QImage(pixels.tobytes(), width, height, pixels.strides[0], QImage.Format.Format_Grayscale8)
        self._pixmap = QPixmap.fromImage(image)
        self._resize_image()

    def _resize_image(self) -> None:
        """
        Fit the LUT-adjusted image into the preview while preserving its aspect ratio.
        """
        if self._pixmap is not None:
            self.image_label.setPixmap(self._pixmap.scaled(self.image_label.size(),
                                                           Qt.AspectRatioMode.KeepAspectRatio,
                                                           Qt.TransformationMode.SmoothTransformation,
                                                           ))

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        """
        Keep the preview fitted when the review tab is resized.
        """
        super().resizeEvent(a0)
        self._resize_image()

    def stop_live_view(self) -> None:
        """
        Stop owned acquisition and restore shutter settings before releasing the worker.
        """
        if self._stopped:
            return
        self.timer.stop()
        try:
            if self._started_sequence:
                try:
                    if self.core.is_sequence_running():
                        self.core.stop_sequence_acquisition()
                finally:
                    self._restore_illumination()
        finally:
            self._stopped = True

    def _restore_illumination(self) -> None:
        """
        Restore each changed illumination setting even if another restoration fails.
        """
        try:
            self.core.set_shutter_open(self._shutter_open)
        finally:
            try:
                self.core.set_auto_shutter(self._auto_shutter)
            finally:
                if self._light_path is not None:
                    self.core.set_property('LappMainBranch1', 'State', self._light_path)

    def _finish(self, result: str) -> None:
        """
        Finish cleanup before returning the user's choice to the pipeline.
        """
        if self.result is not None:
            return
        try:
            self.stop_live_view()
        except Exception:
            logger.exception("Could not clean up live focus acquisition")
            result = "quit"
        self.result = result
        self.result_signal.emit(result)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """
        Treat closing the review as Quit.
        """
        self._finish("quit")
        if a0 is not None:
            a0.accept()


def prompt_live_focus(a1_manager: A1Manager) -> str:
    """
    Run the same live focus review in a standalone window.
    """
    app = QApplication.instance() or QApplication([])
    window = LiveFocusWidget(a1_manager)
    loop = QEventLoop()
    window.result_signal.connect(loop.quit)
    window.resize(800, 650)
    window.show()
    try:
        loop.exec()
        return window.result or "quit"
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()
