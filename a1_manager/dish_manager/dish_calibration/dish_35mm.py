from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field

import logging

from a1_manager.utils.utility_classes import WellCircleCoord, WellSquareCoord
from a1_manager.dish_manager.dish_utils.prompt_utils import prompt_for_edge_points, prompt_for_calibration_approval
from a1_manager.microscope_hardware.nikon import NikonTi2
from a1_manager.dish_manager.dish_calib_manager import DishCalibManager
from a1_manager.dish_manager.dish_utils.geometry_utils import find_circle


SETTINGS_35MM = {'expected_radius': 10.5 * 1000} # in micron

@dataclass
class Dish35mm(DishCalibManager):
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
    
    def _calibrate_dish(self, nikon: NikonTi2) -> dict[str, WellCircleCoord]:  # type: ignore[override]
        """
        Calibrates the 35mm dish by asking for three points along the edge of the circle.
        Returns a dictionary mapping a well identifier (e.g., 'A1') to a WellCircle.
        
        If the measured radius is outside the expected range, the user is prompted to either
        proceed with the measured radius or restart the calibration process.
        """
        center = None
        measured_radius = None
        success_calibration = False    
        while not success_calibration:
            # Define 3 points on the middle ring. The middle of the objective must be on the inner part of the ring
            point1, point2, point3 = prompt_for_edge_points(nikon)
            # Center of circle
            center, measured_radius = find_circle(point1, point2, point3)
            
            if not self.expected_radius_lower < measured_radius < self.expected_radius_upper:
                logging.error(f"\nCalibration failed! Radius={measured_radius} vs expected radius={self.expected_radius}")
                
                # Ask user if they want to proceed with the measured radius or restart
                if prompt_for_calibration_approval(measured_radius, self.expected_radius, 
                                                 self.expected_radius_lower, self.expected_radius_upper):
                    success_calibration = True
                else:
                    continue
            else:
                logging.info(f"\nCalibration successful! Radius={measured_radius} vs expected radius={self.expected_radius}")
                success_calibration = True
        
        assert center is not None, "Center should not be None after successful calibration"
        assert measured_radius is not None, "Measured radius should not be None after successful calibration"
        return {'A1': WellCircleCoord(center=center, radius=measured_radius)}
