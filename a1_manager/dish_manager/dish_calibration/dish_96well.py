from dataclasses import dataclass, field
from string import ascii_uppercase

from dish_manager.dish_utils.prompt_utils import prompt_for_center
from utils.utility_classes import WellCircleCoord
from microscope_hardware.nikon import NikonTi2
from dish_manager.dish_calib_manager import DishCalibManager


SETTINGS_96WELL = {
    "row_number": 8,
    "col_number": 12,
    "well_radius": 7 / 2 * 1000,  # in micron,
    'length': 99.0 * 1000,  # in micron
    'width': 63.0 * 1000}  # in micron

@dataclass
class Dish96well(DishCalibManager):
    row_number: int = field(default_factory=int)
    col_number: int = field(default_factory=int)
    well_radius: float = field(default_factory=float)
    length: float = field(default_factory=float)  # in micron, from center A1 to center A12
    width: float = field(default_factory=float)  # in micron, from center A1 to center H1

    def __post_init__(self) -> None:
        self.unpack_settings(SETTINGS_96WELL)

    def calibrate_dish(self, nikon: NikonTi2, top_left_center: tuple[float,float] | None = None) -> dict[str, WellCircleCoord]:
        """Calibrates a 96-well plate by computing each well's center. If the top-left center is not provided, the user is prompted to move to the A1 well. Returns a dictionary mapping well names (e.g., 'A1', 'B2', etc.) to WellCircle objects."""
        
        x_tl, y_tl = self.get_center_point(nikon, top_left_center)

        # Create wells
        dish_measurements: dict[str, WellCircleCoord] = {}
        for i, letter in enumerate(ascii_uppercase[:self.row_number]):
            for j in range(self.col_number):
                well_number = j + 1
                x_center = x_tl - (self.length / (self.col_number - 1)) * j
                y_center = y_tl + (self.width / (self.row_number - 1)) * i
                dish_measurements[f"{letter}{well_number}"] = WellCircleCoord(center=(x_center, y_center), radius=self.well_radius)

        print(f"Calibration successful!")
        return dish_measurements

    def get_center_point(self, nikon: NikonTi2, top_left_center: tuple[float,float] | None = None) -> tuple[float,float]:
        if top_left_center is None:
            # Define the center of the dish
            return prompt_for_center(nikon)
        return top_left_center