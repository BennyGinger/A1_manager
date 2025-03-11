from dataclasses import dataclass, field
from string import ascii_uppercase

from dish_manager.dish_calibration.well_utils import WellCircle
from dish_manager.dish_calibration.prompt_utils import prompt_for_edge_points, prompt_for_center
from microscope_hardware.nikon import NikonTi2
from a1_manager.dish_manager.dish_calib_manager import DishCalibManager
from dish_manager.dish_calibration.geometry_utils import find_circle


SETTINGS_35MM = {'expected_radius': 10.5 * 1000} # in micron

SETTINGS_96WELL = {
    "row_number": 8,
    "col_number": 12,
    "well_radius": 7 / 2 * 1000,  # in micron,
    'length': 99.0 * 1000,  # in micron
    'width': 63.0 * 1000}  # in micron

@dataclass
class Dish35mm(DishCalibManager):
    
    expected_radius: float = field(default_factory=float)
    expected_radius_upper: float = field(init=False)
    expected_radius_lower: float = field(init=False)
    
    def __post_init__(self)-> None:
        self.unpack_settings(SETTINGS_35MM)
        
        # Determine upper and lower bounds for the expected radius
        correction_percentage: float = 0.05 # decimal percentage
        self.expected_radius_upper = self.expected_radius + (self.expected_radius * correction_percentage)
        self.expected_radius_lower = self.expected_radius - (self.expected_radius * correction_percentage)
    
    def calibrate_dish(self, nikon: NikonTi2, list_points: list[tuple[float, float]] | None = None)-> dict[str, WellCircle]:
        """Calibrates the 35mm dish by asking for three points along the edge of the circle.
        Returns a dictionary mapping a well identifier (e.g., 'A1') to a WellCircle.
        """
        # TODO: Instead of failing the calibration, ask if the user wants to use the measured radius, if yes continue, if no, start again
        success_calibration = False    
        while not success_calibration:
            # Define 3 points on the middle ring. The middle of the objective must be on the inner part of the ring
            point1, point2, point3 = self.get_edge_points(nikon, list_points)
            # Center of circle
            center, measured_radius = find_circle(point1,point2,point3)

            if not self.expected_radius_lower < measured_radius < self.expected_radius_upper:
                print(f"\nCalibration failed, start again! Radius={measured_radius} vs expected radius={self.expected_radius}")
                continue
            
            print(f"\nCalibration successful! Radius={measured_radius} vs expected radius={self.expected_radius}")
            success_calibration = True
        return {'A1': WellCircle(center=center, radius=measured_radius)}

    def get_edge_points(self, nikon: NikonTi2, list_points: list[tuple[float, float]] | None = None) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        if list_points is not None:
            if len(list_points) != 3:
                raise ValueError("List of points must have 3 points of tuple(float,float)")
            
            point1, point2, point3 = list_points
            return point1, point2, point3
        # Prompt the user to move the stage to the edge of the dish
        return prompt_for_edge_points(nikon)

@dataclass
class Dish96well(DishCalibManager):
    row_number: int = field(default_factory=int)
    col_number: int = field(default_factory=int)
    well_radius: float = field(default_factory=float)
    length: float = field(default_factory=float)  # in micron, from center A1 to center A12
    width: float = field(default_factory=float)  # in micron, from center A1 to center H1

    def __post_init__(self) -> None:
        self.unpack_settings(SETTINGS_96WELL)

    def calibrate_dish(self, nikon: NikonTi2, top_left_center: tuple[float,float] | None = None) -> dict[str, WellCircle]:
        """Calibrates a 96-well plate by computing each well's center. If the top-left center is not provided, the user is prompted to move to the A1 well. Returns a dictionary mapping well names (e.g., 'A1', 'B2', etc.) to WellCircle objects."""
        
        x_tl, y_tl = self.get_center_point(nikon, top_left_center)

        # Create wells
        dish_measurements: dict[str, WellCircle] = {}
        for i, letter in enumerate(ascii_uppercase[:self.row_number]):
            for j in range(self.col_number):
                well_number = j + 1
                x_center = x_tl - (self.length / (self.col_number - 1)) * j
                y_center = y_tl + (self.width / (self.row_number - 1)) * i
                dish_measurements[f"{letter}{well_number}"] = WellCircle(center=(x_center, y_center), radius=self.well_radius)

        print(f"Calibration successful!")
        return dish_measurements

    def get_center_point(self, nikon: NikonTi2, top_left_center: tuple[float,float] | None = None) -> tuple[float,float]:
        if top_left_center is None:
            # Define the center of the dish
            return prompt_for_center(nikon)
        return top_left_center