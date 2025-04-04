from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field

from utils.utility_classes import WellCircleCoord
from dish_manager.dish_utils.prompt_utils import prompt_for_edge_points
from microscope_hardware.nikon import NikonTi2
from dish_manager.dish_calib_manager import DishCalibManager
from dish_manager.dish_utils.geometry_utils import find_circle


SETTINGS_35MM = {'expected_radius': 10.5 * 1000} # in micron

@dataclass
class Dish35mm(DishCalibManager, dish_name='35mm'):
    """
    Calibration handler for the 35mm dish.
    
    Attributes:
    - expected_radius (float): Expected radius of the dish (in microns).
    - expected_radius_upper (float): Upper bound for the expected radius.
    - expected_radius_lower (float): Lower bound for the expected radius.
    """
    
    expected_radius: float = field(default_factory=float)
    expected_radius_upper: float = field(init=False)
    expected_radius_lower: float = field(init=False)
    
    def __post_init__(self)-> None:
        self.unpack_settings(SETTINGS_35MM)
        
        # Determine upper and lower bounds for the expected radius
        correction_percentage: float = 0.05 # decimal percentage
        self.expected_radius_upper = self.expected_radius + (self.expected_radius * correction_percentage)
        self.expected_radius_lower = self.expected_radius - (self.expected_radius * correction_percentage)
    
    def calibrate_dish(self, nikon: NikonTi2)-> dict[str, WellCircleCoord]:
        """
        Calibrates the 35mm dish by asking for three points along the edge of the circle.
        Returns a dictionary mapping a well identifier (e.g., 'A1') to a WellCircle.
        """
        # TODO: Instead of failing the calibration, ask if the user wants to use the measured radius, if yes continue, if no, start again
        success_calibration = False    
        while not success_calibration:
            # Define 3 points on the middle ring. The middle of the objective must be on the inner part of the ring
            point1, point2, point3 = prompt_for_edge_points(nikon)
            # Center of circle
            center, measured_radius = find_circle(point1, point2, point3)
            
            if not self.expected_radius_lower < measured_radius < self.expected_radius_upper:
                print(f"\nCalibration failed, start again! Radius={measured_radius} vs expected radius={self.expected_radius}")
                continue
            
            print(f"\nCalibration successful! Radius={measured_radius} vs expected radius={self.expected_radius}")
            success_calibration = True
        return {'A1': WellCircleCoord(center=center, radius=measured_radius)}
