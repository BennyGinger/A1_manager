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
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QSlider, QHBoxLayout, QPushButton

logger = logging.getLogger(__name__)

DISTANCE_TO_LIQUID = {'96well': 16_000.0, '384well' : 16000}


# ==============================================================================
# REUSABLE CORE: Frame Extraction & Overlay Processor Engine
# ==============================================================================
def process_mm_frame_to_pixmap(
    tagged_img, 
    show_crosshairs: bool = False, 
    target_radius: int | None = None,
    well_lines: dict | None = None  # Added dictionary for our 4 adjustable lines
) -> QPixmap | None:
    """
    Extracts a Micro-Manager image matrix and applies optional overlays.
    Returns a QPixmap ready for PyQt rendering, or None if extraction fails.
    """
    try:
        width = tagged_img.tags["Width"]
        height = tagged_img.tags["Height"]

        # Parse bit depth safely
        if tagged_img.tags["PixelType"] == "GRAY8":
            img = np.reshape(tagged_img.pix, (height, width)).astype(np.uint8)
        else:
            img_16 = np.reshape(tagged_img.pix, (height, width)).astype(np.uint16)
            img = (img_16 / 256).astype(np.uint8)

        color_frame = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        center_x, center_y = int(width / 2), int(height / 2)

        # Color definitions (BGR)
        red_solid = (0, 0, 255)
        green_faint = (0, 180, 0)
        green_bright = (0, 255, 0)  # Added bright green for adjustable layout lines
        red_faint = (50, 50, 180)

        # Optional Overlay 1: Green Crosshairs & Tick Marks
        if show_crosshairs:
            cv2.circle(color_frame, (center_x, center_y), 4, green_faint, -1)
            cv2.line(color_frame, (center_x - 100, center_y), (center_x + 100, center_y), green_faint, 1)
            cv2.line(color_frame, (center_x, center_y - 100), (center_x, center_y + 100), green_faint, 1)

            for offset in [-80, -40, 40, 80]:
                cv2.line(color_frame, (center_x + offset, center_y - 5), (center_x + offset, center_y + 5), green_faint, 1)
                cv2.line(color_frame, (center_x - 5, center_y + offset), (center_x + 5, center_y + offset), green_faint, 1)

        # NEW: Adjustable Green Reference Lines for Well Corners
        if well_lines:
            # Horizontal line 1 (Top Side)
            cv2.line(color_frame, (0, well_lines['h1']), (width, well_lines['h1']), green_bright, 1)
            # Horizontal line 2 (Bottom Side)
            cv2.line(color_frame, (0, well_lines['h2']), (width, well_lines['h2']), green_bright, 1)
            # Vertical line 1 (Left Side)
            cv2.line(color_frame, (well_lines['v1'], 0), (well_lines['v1'], height), green_bright, 1)
            # Vertical line 2 (Right Side)
            cv2.line(color_frame, (well_lines['v2'], 0), (well_lines['v2'], height), green_bright, 1)

        # Optional Overlay 2: Dynamic Bullseye Alignment Target Circles
        if target_radius is not None and target_radius > 0:
            cv2.circle(color_frame, (center_x, center_y), max(10, target_radius - 20), red_faint, 1, cv2.LINE_AA)
            cv2.circle(color_frame, (center_x, center_y), target_radius + 20, red_faint, 1, cv2.LINE_AA)
            cv2.circle(color_frame, (center_x, center_y), target_radius, red_solid, 2, cv2.LINE_AA)

        # Convert finalized matrix to PyQt QPixmap format
        rgb_image = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qt_image)
        
    except Exception as e:
        logger.error(f"Failed to process live stream frame: {e}")
        return None


# ==============================================================================
# NEW MODULE: Highly Configurable Base Live View Window with Quit Button
# ==============================================================================
class LiveViewPopup(QMainWindow):
    """
    A generic, reusable window that automatically handles MM video streams.
    Can be used directly or subclassed to add target overlays/sliders.
    """
    def __init__(self, core: Core, title: str = "Live Feed", show_crosshairs: bool = True):
        super().__init__()
        self.mmc = core
        self.show_crosshairs = show_crosshairs

        self.setWindowTitle(title)
        self.setGeometry(150, 150, 800, 720)
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

        # Custom controls container (Subclasses insert extra UI widgets here)
        self.controls_layout = QVBoxLayout()
        self.main_layout.addLayout(self.controls_layout)

        # Explicit Universal Quit Button
        self.quit_button = QPushButton("Quit Live View")
        self.quit_button.setStyleSheet("font-weight: bold; background-color: #d9534f; color: white; padding: 6px;")
        self.quit_button.clicked.connect(self.close)
        self.main_layout.addWidget(self.quit_button)

        # Micro-Manager Live Stream Safety Check
        self.was_sequence_running = self.mmc.is_sequence_running()
        if not self.was_sequence_running:
            self.mmc.start_continuous_sequence_acquisition(0)

        # 30 FPS Update Loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_frame)
        self.timer.start(33)

    def get_target_radius(self) -> int | None:
        """Override in subclasses to return a radius to draw a target circle."""
        return None

    def get_well_lines(self) -> dict | None:
        """Override in subclasses to pass custom lines positions to renderer."""
        return None

    def update_live_frame(self):
        if self.mmc.get_remaining_image_count() == 0:
            return

        tagged_img = self.mmc.get_last_tagged_image()
        pixmap = process_mm_frame_to_pixmap(
            tagged_img=tagged_img, 
            show_crosshairs=self.show_crosshairs, 
            target_radius=self.get_target_radius(),
            well_lines=self.get_well_lines()  # Added mapping argument
        )
        
        if pixmap:
            self.image_label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.timer.stop()
        if not self.was_sequence_running and self.mmc.is_sequence_running():
            self.mmc.stop_sequence_acquisition()
        event.accept()


# ==============================================================================
# UPGRADED: Enhanced Alignment Window using the New Reusable Architecture
# ==============================================================================
class AdvancedAlignmentPopup(LiveViewPopup):
    """
    Subclass that adds a specific slider layout to control the target circle radius.
    """
    def __init__(self, core: Core, initial_radius: int = 80):
        # Initialize base window with crosshairs turned ON
        super().__init__(core, title="Piezohead Bullseye Alignment Tool", show_crosshairs=True)
        self.current_radius = initial_radius

        # Build Interactive Radius Slider Panel with Numerical Readout
        self.slider_layout = QHBoxLayout()

        slider_title = QLabel("Target Circle Size: ")
        self.slider_layout.addWidget(slider_title)

        self.radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.radius_slider.setMinimum(10)
        self.radius_slider.setMaximum(300)
        self.radius_slider.setValue(self.current_radius)
        self.radius_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.radius_slider.setTickInterval(20)
        self.radius_slider.valueChanged.connect(self.update_radius)
        self.slider_layout.addWidget(self.radius_slider)

        self.value_label = QLabel(f"<b>{self.current_radius} px</b>")
        self.value_label.setFixedWidth(60)
        self.slider_layout.addWidget(self.value_label)

        # Inject into the base class's designated controls container layout
        self.controls_layout.addLayout(self.slider_layout)

    def update_radius(self, value):
        self.current_radius = value
        self.value_label.setText(f"<b>{value} px</b>")

    def get_target_radius(self) -> int:
        """Expose the variable radius to the parent processing loop."""
        return self.current_radius


# ==============================================================================
# NEW SUBCLASS: Virtual Well Corner Alignment Tool
# ==============================================================================
class WellCornerAlignmentPopup(LiveViewPopup):
    """
    Subclass that displays four independent green lines to capture 
    the straight edges of a well with rounded corners.
    """
    def __init__(self, core: Core):
        super().__init__(core, title="384-Well Plate Corner Alignment Tool", show_crosshairs=True)
        
        # Hardcoding standard dimensions based on typical MM cameras (e.g., 1024 or 2048)
        # It updates dynamically, but lets assume defaults until first frame renders
        self.img_w = 1200
        self.img_h = 1000
        # Initial baseline positions for the 4 sides of the well layout
        self.h1_val = int(self.img_h * 0.25)
        self.h2_val = int(self.img_h * 0.75)
        self.v1_val = int(self.img_w * 0.25)
        self.v2_val = int(self.img_w * 0.75)

        # Construct structural slider UI grids
        self.setup_sliders()

    def setup_sliders(self):
        # Master grid for layouts
        panel = QVBoxLayout()
        
        # Build horizontal controls group
        h1_box = QHBoxLayout()
        h1_box.addWidget(QLabel("Top Edge (H1):"))
        self.h1_slider = QSlider(Qt.Orientation.Horizontal)
        self.h1_slider.setRange(0, self.img_h)
        self.h1_slider.setValue(self.h1_val)
        self.h1_slider.valueChanged.connect(self.update_lines)
        h1_box.addWidget(self.h1_slider)
        panel.addLayout(h1_box)
        
        h2_box = QHBoxLayout()
        h2_box.addWidget(QLabel("Bottom Edge (H2):"))
        self.h2_slider = QSlider(Qt.Orientation.Horizontal)
        self.h2_slider.setRange(0, self.img_h)
        self.h2_slider.setValue(self.h2_val)
        self.h2_slider.valueChanged.connect(self.update_lines)
        h2_box.addWidget(self.h2_slider)
        panel.addLayout(h2_box)
        
        # Build vertical controls group
        v1_box = QHBoxLayout()
        v1_box.addWidget(QLabel("Left Edge (V1):"))
        self.v1_slider = QSlider(Qt.Orientation.Horizontal)
        self.v1_slider.setRange(0, self.img_w)
        self.v1_slider.setValue(self.v1_val)
        self.v1_slider.valueChanged.connect(self.update_lines)
        v1_box.addWidget(self.v1_slider)
        panel.addLayout(v1_box)
        
        v2_box = QHBoxLayout()
        v2_box.addWidget(QLabel("Right Edge (V2):"))
        self.v2_slider = QSlider(Qt.Orientation.Horizontal)
        self.v2_slider.setRange(0, self.img_w)
        self.v2_slider.setValue(self.v2_val)
        self.v2_slider.valueChanged.connect(self.update_lines)
        v2_box.addWidget(self.v2_slider)
        panel.addLayout(v2_box)
        
        self.controls_layout.addLayout(panel)

    def update_lines(self):
        # Sync slider configurations to variables
        self.h1_val = self.h1_slider.value()
        self.h2_val = self.h2_slider.value()
        self.v1_val = self.v1_slider.value()
        self.v2_val = self.v2_slider.value()

    def get_well_lines(self) -> dict:
        """Expose current lines metrics back to the core processor routine."""
        return {
            'h1': self.h1_val,
            'h2': self.h2_val,
            'v1': self.v1_val,
            'v2': self.v2_val
        }

    def update_live_frame(self):
        """Extended check to calibrate slider limits to dynamic metadata width/height."""
        if self.mmc.get_remaining_image_count() == 0:
            return
            
        tagged_img = self.mmc.get_last_tagged_image()
        h = tagged_img.tags["Height"]
        w = tagged_img.tags["Width"]
        
        # If resolution shifts, expand slider parameters
        if h != self.img_h or w != self.img_w:
            self.img_h = h
            self.img_w = w
            self.h1_slider.setMaximum(h)
            self.h2_slider.setMaximum(h)
            self.v1_slider.setMaximum(w)
            self.v2_slider.setMaximum(w)
            
        pixmap = process_mm_frame_to_pixmap(
            tagged_img=tagged_img,
            show_crosshairs=self.show_crosshairs,
            target_radius=None,
            well_lines=self.get_well_lines()
        )
        
        if pixmap:
            self.image_label.setPixmap(pixmap)

# ==============================================================================
# CONVENIENCE ENGINE RUNNERS
# ==============================================================================
def run_well_corner_alignment_gui(core: Core):
    """Launches the window featuring the green adjustable lines layout."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = WellCornerAlignmentPopup(core)
    window.show()
    app.exec()

def run_alignment_gui(core: Core, ring_radius: int = 80):
    """Launches the window featuring crosshairs AND the slider circle target."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = AdvancedAlignmentPopup(core, initial_radius=ring_radius)
    window.show()
    app.exec()

def run_simple_live_view(core: Core, show_crosshairs: bool = True):
    """Launches a pure streaming preview containing just a stop button and crosshair toggle."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = LiveViewPopup(core, title="Hardware Stream Preview", show_crosshairs=show_crosshairs)
    window.show()
    app.exec()

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", message=".*Java ZMQ server and Python client.*")
    from a1_manager import A1Manager

    a1_manager = A1Manager(objective='10x', lamp_name='pE-800')
    
    # CHANGED: Swapped to launch your new corner alignment view instead of simple view
    run_well_corner_alignment_gui(core=a1_manager.core)


