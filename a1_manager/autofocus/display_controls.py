from __future__ import annotations

from PyQt6.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel, QPushButton, QSlider, QSpinBox


class DisplayControls(QGroupBox):
    """
    Adjust live image levels, brightness, and contrast independently of acquisition.
    """

    changed = pyqtSignal()
    auto_scale_requested = pyqtSignal()

    def __init__(self) -> None:
        """
        Build matching slider and numeric controls for camera intensity levels.
        """
        super().__init__("Display LUT")
        self._layout = QGridLayout(self)
        self.min_slider, self.min_value = self._add_control("Min", 0, 65534, 0)
        self.max_slider, self.max_value = self._add_control("Max", 1, 65535, 65535)
        self.brightness_slider, self.brightness_value = self._add_control("Brightness", 2, 100, 50)
        self.contrast_slider, self.contrast_value = self._add_control("Contrast", 3, 100, 50)
        self.max_slider.setMinimum(1)
        self.max_value.setMinimum(1)
        self.min_slider.valueChanged.connect(self._minimum_changed)
        self.max_slider.valueChanged.connect(self._maximum_changed)
        self.auto_scale_button = QPushButton("Auto-scale")
        self.auto_scale_button.clicked.connect(self.auto_scale_requested.emit)
        self._layout.addWidget(self.auto_scale_button, 4, 0, 1, 3)

    def _add_control(self, label: str, row: int, maximum: int, value: int) -> tuple[QSlider, QSpinBox]:
        """
        Add a synchronized slider and exact numeric entry.
        """
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, maximum)
        slider.setValue(value)
        spin = QSpinBox()
        spin.setRange(0, maximum)
        spin.setValue(value)
        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(self.changed.emit)
        self._layout.addWidget(QLabel(label), row, 0)
        self._layout.addWidget(slider, row, 1)
        self._layout.addWidget(spin, row, 2)
        return slider, spin

    def _minimum_changed(self, value: int) -> None:
        """
        Keep the white level strictly above the black level.
        """
        self.max_slider.setMinimum(value + 1)
        self.max_value.setMinimum(value + 1)

    def _maximum_changed(self, value: int) -> None:
        """
        Keep the black level strictly below the white level.
        """
        self.min_slider.setMaximum(value - 1)
        self.min_value.setMaximum(value - 1)

    def set_levels(self, minimum: int, maximum: int, full_range: int) -> None:
        """
        Set an automatically chosen range and reset brightness and contrast.
        """
        controls = (self.min_slider, self.min_value, self.max_slider, self.max_value,
                    self.brightness_slider, self.contrast_slider)
        blockers = [QSignalBlocker(control) for control in controls]
        with QSignalBlocker(self):
            self.min_slider.setRange(0, maximum - 1)
            self.min_value.setRange(0, maximum - 1)
            self.max_slider.setRange(minimum + 1, full_range)
            self.max_value.setRange(minimum + 1, full_range)
            self.min_slider.setValue(minimum)
            self.min_value.setValue(minimum)
            self.max_slider.setValue(maximum)
            self.max_value.setValue(maximum)
            self.brightness_slider.setValue(50)
            self.contrast_slider.setValue(50)
            self.brightness_value.setValue(50)
            self.contrast_value.setValue(50)
        del blockers
        self.changed.emit()
