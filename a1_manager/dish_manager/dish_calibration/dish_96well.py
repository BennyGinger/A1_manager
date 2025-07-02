from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
from string import ascii_uppercase
import logging

from a1_manager.dish_manager.dish_utils.prompt_utils import prompt_for_center
from a1_manager.utils.utility_classes import WellCircleCoord
from a1_manager.microscope_hardware.nikon import NikonTi2
from a1_manager.dish_manager.dish_calib_manager import DishCalibManager


SETTINGS_96WELL = {
    "row_number": 8,
    "col_number": 12,
    "well_radius": 7 / 2 * 1000,  # in micron,
    'length': 99.0 * 1000,  # in micron
    'width': 63.0 * 1000  # in micron
    }

@dataclass
class Dish96well(DishCalibManager):
    """
    Calibration handler for the 96-well plate.
    
    Attributes:
    - row_number (int): Number of rows in the dish.
    - col_number (int): Number of columns in the dish.
    - well_radius (float): Radius of the well (in microns).
    - length (float): Length of the dish along the x-axis (in microns).
    - width (float): Width of the dish along the y-axis (in microns).
    """
    
    row_number: int = field(default_factory=int)
    col_number: int = field(default_factory=int)
    well_radius: float = field(default_factory=float)
    length: float = field(default_factory=float)  # in micron, from center A1 to center A12
    width: float = field(default_factory=float)  # in micron, from center A1 to center H1

    def __post_init__(self) -> None:
        self.unpack_settings(SETTINGS_96WELL)

    def _calibrate_dish(self, nikon: NikonTi2) -> dict[str, WellCircleCoord]:  # type: ignore[override]
        """
        Calibrates a 96-well plate by computing each well's center.
        If the top-left center is not provided, the user is prompted to move to the A1 well.
        Returns a dictionary mapping well names (e.g., 'A1', 'B2', etc.) to WellCircle objects.
        """
        
        x_tl, y_tl = prompt_for_center(nikon)

        # Create wells
        dish_measurements: dict[str, WellCircleCoord] = {}
        for i, letter in enumerate(ascii_uppercase[:self.row_number]):
            for j in range(self.col_number):
                well_number = j + 1
                x_center = x_tl - (self.length / (self.col_number - 1)) * j
                y_center = y_tl + (self.width / (self.row_number - 1)) * i
                dish_measurements[f"{letter}{well_number}"] = WellCircleCoord(
                    center=(x_center, y_center),
                    radius=self.well_radius
                    )

        logging.info("Calibration successful for the 96-well plate.")
        return dish_measurements
