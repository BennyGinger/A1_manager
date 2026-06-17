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
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtWidgets import (QApplication, QLabel, QMainWindow, QVBoxLayout, 
                             QWidget, QSlider, QHBoxLayout, QFrame, QCheckBox, 
                             QPushButton, QDialog, QMessageBox)

logger = logging.getLogger(__name__)

DISTANCE_TO_LIQUID = {'96well': 16_000.0, '384well' : 16000}

# ==============================================================================
# NEW: PRE-FLIGHT CHECKLIST DIALOG
# ==============================================================================
class PreFlightChecklist(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pre-Run Hardware Verification")
        self.setFixedSize(420, 220)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header title
        title = QLabel("Verify Hardware Setup Before Starting:")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Checkboxes
        self.check_plate = QCheckBox("A 96-well plate is currently loaded in the stage.")
        self.check_plate.setFont(QFont("Arial", 10))
        
        self.check_liquid = QCheckBox("Well A1 contains exactly 90 µL of liquid.")
        self.check_liquid.setFont(QFont("Arial", 10))
        
        layout.addWidget(self.check_plate)
        layout.addWidget(self.check_liquid)
        
        # Connect checkbox states to toggle the Start button
        self.check_plate.stateChanged.connect(self.validate_checks)
        self.check_liquid.stateChanged.connect(self.validate_checks)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Initialize Arm & Begin")
        self.btn_start.setEnabled(False) # Locked until boxes are checked
        self.btn_start.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Cancel Run")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_start)
        layout.addLayout(btn_layout)

    def validate_checks(self):
        """Enable the start button only when all conditions are fulfilled."""
        all_checked = self.check_plate.isChecked() and self.check_liquid.isChecked()
        self.btn_start.setEnabled(all_checked)

def verify_hardware_setup() -> bool:
    """Helper to launch the verification check. Returns True if confirmed."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    dialog = PreFlightChecklist()
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted


# ==============================================================================
# INTERACTIVE BULLSEYE ALIGNMENT WINDOW
# ==============================================================================
class AdvancedAlignmentPopup(QMainWindow):
    def __init__(self, core: Core, initial_radius: int = 80):
        super().__init__()
        self.mmc = core
        self.current_radius = initial_radius

        self.setWindowTitle("Piezohead Bullseye Alignment Tool")
        self.setGeometry(100, 100, 1100, 680)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_horizontal_layout = QHBoxLayout(self.central_widget)
        self.main_horizontal_layout.setContentsMargins(15, 15, 15, 15)
        self.main_horizontal_layout.setSpacing(20)

        # LEFT COLUMN (Camera view & slider)
        self.left_column = QVBoxLayout()
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_column.addWidget(self.image_label)

        self.slider_layout = QHBoxLayout()
        slider_title = QLabel("Target Circle Size: ")
        self.slider_layout.addWidget(slider_title)

        self.radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.radius_slider.setMinimum(10)
        self.radius_slider.setMaximum(500)
        self.radius_slider.setValue(self.current_radius)
        self.radius_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.radius_slider.setTickInterval(20)
        self.radius_slider.valueChanged.connect(self.update_radius)
        self.slider_layout.addWidget(self.radius_slider)

        self.value_label = QLabel(f"<b>{self.current_radius} px</b>")
        self.value_label.setFixedWidth(60)
        self.slider_layout.addWidget(self.value_label)
        self.left_column.addLayout(self.slider_layout)

        self.main_horizontal_layout.addLayout(self.left_column, stretch=3)

        # RIGHT COLUMN (Instructions panel)
        self.right_column = QVBoxLayout()
        instruction_frame = QFrame()
        instruction_frame.setFrameShape(QFrame.Shape.StyledPanel)
        instruction_frame.setStyleSheet("background-color: #FAFAFA; border-radius: 8px;")
        
        frame_layout = QVBoxLayout(instruction_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(12)

        header = QLabel("Alignment Instructions")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #2C3E50;")
        frame_layout.addWidget(header)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #BDC3C7;")
        frame_layout.addWidget(line)

        guide_text = """
        <p><b>1. Match the Target Circle:</b><br>
        Adjust the slider under the camera view until the red circle perfectly overlaps your physical light ring.</p>
        
        <p><b>2. Align to Center (X/Y Knobs):</b><br>
        Use the manual thumb screws on the piezohead block to center the ring on the target bullseye.
        <ul>
          <li><b>Clockwise X-screw:</b> Moves light ring to the <b>RIGHT</b></li>
          <li><b>Counter-Clockwise X-screw:</b> Moves light ring to the <b>LEFT</b></li>
          <li><b>Clockwise Y-screw:</b> Moves light ring <b>UPWARD</b></li>
          <li><b>Counter-Clockwise Y-screw:</b> Moves light ring <b>DOWNWARD</b></li>
        </ul></p>
        
        <p style="color: #C0392B; background-color: #FDEDEC; padding: 10px; border-radius: 4px; border: 1px solid #FADBD8;">
        <b>⚠️ LOST THE LIGHT RING? (OUT OF FOV)</b><br>
        If the ring is completely missing from the screen:<br>
        1. Open <b>A1manager</b> software.<br>
        2. Change the microscope objective configuration to <b>4x</b>.<br>
        3. This expands the field of view so you can catch the edge of the ring, bring it closer to the center, and then switch back to your operational objective.
        </p>
        
        <p><b>3. Complete Alignment:</b><br>
        Once the ring is perfectly centered on the crosshairs, close this window. Your script will automatically resume standard automation.</p>
        """
        
        instructions_body = QLabel(guide_text)
        instructions_body.setFont(QFont("Arial", 10))
        instructions_body.setWordWrap(True)
        instructions_body.setTextFormat(Qt.TextFormat.RichText)
        frame_layout.addWidget(instructions_body)
        frame_layout.addStretch()

        self.right_column.addWidget(instruction_frame)
        self.main_horizontal_layout.addLayout(self.right_column, stretch=2)

        self.was_sequence_running = self.mmc.is_sequence_running()
        if not self.was_sequence_running:
            self.mmc.start_continuous_sequence_acquisition(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_frame)
        self.timer.start(33)

    def update_radius(self, value):
        self.current_radius = value
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
            img_16 = np.reshape(tagged_img.pix, (height, width)).astype(np.uint16)
            img = (img_16 / 256).astype(np.uint8)

        color_frame = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        center_x, center_y = int(width / 2), int(height / 2)

        red_solid = (0, 0, 255)
        green_faint = (0, 180, 0)
        red_faint = (50, 50, 180)

        cv2.circle(color_frame, (center_x, center_y), max(10, self.current_radius - 20), red_faint, 1, cv2.LINE_AA)
        cv2.circle(color_frame, (center_x, center_y), self.current_radius + 20, red_faint, 1, cv2.LINE_AA)
        cv2.circle(color_frame, (center_x, center_y), self.current_radius, red_solid, 2, cv2.LINE_AA)
        cv2.circle(color_frame, (center_x, center_y), 4, green_faint, -1)

        cv2.line(color_frame, (center_x - 100, center_y), (center_x + 100, center_y), green_faint, 1)
        cv2.line(color_frame, (center_x, center_y - 100), (center_x, center_y + 100), green_faint, 1)

        for offset in [-80, -40, 40, 80]:
            cv2.line(color_frame, (center_x + offset, center_y - 5), (center_x + offset, center_y + 5), green_faint, 1)
            cv2.line(color_frame, (center_x - 5, center_y + offset), (center_x + 5, center_y + offset), green_faint, 1)

        rgb_image = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
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
    from a1_manager import A1Manager, StageCoord
    a1_manager = A1Manager(objective='10x', lamp_name='pE-800')
    
    a1_manager.set_stage_position(StageCoord(xy=[49205.4, -32139.4]))
    
    # 0. Trigger the safety pre-flight hardware checks first
    print("Launching pre-flight verification...")
    if not verify_hardware_setup():
        print("\n[ABORTED] User cancelled the run or hardware verification failed.")
        sys.exit(0)
    
    print("\n[VERIFIED] Setup confirmed by user. Connecting to Micro-Manager hardware...")
    
    

    # 2. Setup and run hardware adjustments safely
    
    core_instance = a1_manager.core
    arm = MarZ(core=core_instance, dish='96well') # type: ignore
    a1_manager.oc_settings('GFP')
    
    print("Current head position:", arm._get_arm_position)
    
    print("Moving arm down to liquid position...")
    arm.to_liquid()
    
    print("\n--- LAUNCHING ADVANCED ALIGNMENT MODULE ---")
    run_alignment_gui(core=core_instance, ring_radius=239)
    
    print("\nAlignment window closed. Returning arm home...")
    arm.to_home()
