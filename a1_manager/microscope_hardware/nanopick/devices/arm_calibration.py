from __future__ import annotations
import sys
import logging
from dataclasses import dataclass, field
from time import sleep
import warnings
import numpy as np
import cv2

warnings.filterwarnings("ignore", message=".*Java ZMQ server and Python client.*")

from pycromanager import Core
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QSlider, QHBoxLayout

logger = logging.getLogger(__name__)

DISTANCE_TO_LIQUID = {'96well': 16_000.0, '384well' : 16000}

# ==============================================================================
# UPGRADED: Enhanced Alignment Window with Slider & Target Grid
# ==============================================================================
class AdvancedAlignmentPopup(QMainWindow):

    def __init__(self, core: Core, initial_radius: int = 80):
        super().__init__()
        self.mmc = core
        self.current_radius = initial_radius

        self.setWindowTitle("Piezohead Bullseye Alignment Tool")
        self.setGeometry(150, 150, 800, 680)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # Main Layout Setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Video Display Label
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.image_label)

        # Interactive Radius Slider Panel with Numerical Readout
        self.slider_layout = QHBoxLayout()

        # 1. Static Prefix Label
        slider_title = QLabel("Target Circle Size: ")
        self.slider_layout.addWidget(slider_title)

        # 2. The Slider Widget
        self.radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.radius_slider.setMinimum(10)
        self.radius_slider.setMaximum(300)
        self.radius_slider.setValue(self.current_radius)
        self.radius_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.radius_slider.setTickInterval(20)
        self.radius_slider.valueChanged.connect(self.update_radius)
        self.slider_layout.addWidget(self.radius_slider)

        # 3. Dynamic Number Value Label
        self.value_label = QLabel(f"<b>{self.current_radius} px</b>")
        # Fixed width prevents the layout from shifting when text size changes
        self.value_label.setFixedWidth(60)
        self.slider_layout.addWidget(self.value_label)

        self.main_layout.addLayout(self.slider_layout)

        # Micro-Manager Live Stream Safety Check
        self.was_sequence_running = self.mmc.is_sequence_running()
        if not self.was_sequence_running:
            self.mmc.start_continuous_sequence_acquisition(0)

        # 30 FPS Update Loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_frame)
        self.timer.start(33)

    def update_radius(self, value):
        """Callback to handle slider movements and update numbers."""
        self.current_radius = value
        # Update the text label dynamically with bold formatting
        self.value_label.setText(f"<b>{value} px</b>")

    def update_live_frame(self):
        if self.mmc.get_remaining_image_count() == 0:
            return

        tagged_img = self.mmc.get_last_tagged_image()
        width = tagged_img.tags["Width"]
        height = tagged_img.tags["Height"]

        if tagged_img.tags["PixelType"] == "GRAY8":
            img = np.reshape(tagged_img.pix, (height, width)).astype(np.uint8)
        else:
            img_16 = np.reshape(tagged_img.pix, (height, width)).astype(
                np.uint16
            )
            img = (img_16 / 256).astype(np.uint8)

        color_frame = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        center_x, center_y = int(width / 2), int(height / 2)

        # Color definitions (BGR)
        red_solid = (0, 0, 255)
        green_faint = (0, 180, 0)
        red_faint = (50, 50, 180)

        # Draw Helper Concentric Bullseye Rings
        cv2.circle(
            color_frame,
            (center_x, center_y),
            max(10, self.current_radius - 20),
            red_faint,
            1,
            cv2.LINE_AA,
        )
        cv2.circle(
            color_frame,
            (center_x, center_y),
            self.current_radius + 20,
            red_faint,
            1,
            cv2.LINE_AA,
        )

        # Draw Primary Alignment Circle & Core Dot
        cv2.circle(
            color_frame,
            (center_x, center_y),
            self.current_radius,
            red_solid,
            2,
            cv2.LINE_AA,
        )
        cv2.circle(color_frame, (center_x, center_y), 4, green_faint, -1)

        # Draw Extended Precision Crosshairs with Measurement Ticks
        cv2.line(
            color_frame,
            (center_x - 100, center_y),
            (center_x + 100, center_y),
            green_faint,
            1,
        )
        cv2.line(
            color_frame,
            (center_x, center_y - 100),
            (center_x, center_y + 100),
            green_faint,
            1,
        )

        for offset in [-80, -40, 40, 80]:
            cv2.line(
                color_frame,
                (center_x + offset, center_y - 5),
                (center_x + offset, center_y + 5),
                green_faint,
                1,
            )
            cv2.line(
                color_frame,
                (center_x - 5, center_y + offset),
                (center_x + 5, center_y + offset),
                green_faint,
                1,
            )

        # Render onto PyQt Layout
        rgb_image = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_image = QImage(
            rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888
        )
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.timer.stop()
        if not self.was_sequence_running and self.mmc.is_sequence_running():
            self.mmc.stop_sequence_acquisition()
        event.accept()


def run_alignment_gui(core: Core, ring_radius: int = 80):
    app = QApplication.instance()
    if not app: 
        app = QApplication(sys.argv)
    window = AdvancedAlignmentPopup(core, initial_radius=ring_radius)
    window.show()
    app.exec()


# ==============================================================================
# Your MarZ Hardware Class (with @property syntax fix applied)
# ==============================================================================
@dataclass(slots=True)
class MarZ():
    core: Core
    dish: str
    _ref_position: float = field(init=False)

    def __post_init__(self):
        self.core.set_property('ZAxis', 'SpeedZ [mm/s]', 18) # type: ignore
        self.core.set_property('ZAxis', 'Acceleration Z [m/s^2]', 0.18) # type: ignore
        self._init_ref_position()
        logger.debug(f"Arm initialized at reference position: {self._ref_position}")
    
    def _init_ref_position(self) -> None:
        self._set_arm_position(100000)
        self.core.wait_for_device('ZAxis') # type: ignore
        self._set_arm_position(round(self._get_arm_position - 5000))
        self.core.wait_for_device('ZAxis') # type: ignore
        self._set_arm_position(100000)
        self.core.wait_for_device('ZAxis') # type: ignore
        self._set_arm_position(round(self._get_arm_position - 500))
        self._ref_position = self._get_arm_position
    
    @property
    def _get_arm_position(self) -> float:
        return self.core.get_position('ZAxis') # type: ignore
    
    def to_liquid(self) -> None:
        return self._set_arm_position(self._ref_position - DISTANCE_TO_LIQUID[self.dish])

    def to_home(self) -> None:
        return self._set_arm_position(self._ref_position)
    
    def _set_arm_position(self, position: float) -> None:
        self.core.set_position('ZAxis', position) # type: ignore
        self.core.wait_for_device('ZAxis') # type: ignore
    
    def safe_check(self) -> None:
        # Note: Fixed property access here to cleanly compare floats
        if self._get_arm_position < self._ref_position:
            logger.warning("The arm is too low, it will be sent home!")
            self._set_arm_position(self._ref_position)
            
if __name__ == "__main__":
    
    from a1_manager import A1Manager
    a1_manager = A1Manager(objective='10x', lamp_name='pE-800')
    
    core_instance = Core()
    arm = MarZ(core=core_instance, dish='96well') # type: ignore

    print("Current head position:", arm._get_arm_position)
    print("Moving arm down to liquid position...")
    arm.to_liquid()
    
    print("\n--- LAUNCHING ADVANCED ALIGNMENT TARGET PANEL ---")
    print("1. Use the slider at the bottom to snap the red circle size to your light ring (if needed).")
    print("2. Adjust physical piezohead knobs to fit the light ring to the target.")
    print("3. Close the target window when the adjustment is completed to continue.")
    
    # Launching with a starting radius guess of 90 pixels
    run_alignment_gui(core=core_instance, ring_radius=237)
    
    print("\nAlignment window closed. Returning arm home...")
    arm.to_home()


    # Smaller screw at the top is responsible for the left-right adjustment: 
    #   - If you turn the screw towards you, it goes to the right in the screen. 
    #   - If you turn it towards the wall, it goes to the left in the screen.
    # Bigger screw at the bottom is responsible for the up-down adjustment:
    #   - If you turn the screw towards you, it goes up in the screen.  
    #   - If you turn the screw towards the wall, it goes down in the screen.   
    