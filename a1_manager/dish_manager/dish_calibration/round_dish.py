from dataclasses import dataclass, field
from string import ascii_uppercase

from microscope_hardware.nikon import NikonTi2
from dish_manager.dish_calib import DishCalib


SETTINGS_35MM = {'expected_radius': 10.5 * 1000} # in micron

SETTINGS_96WELL = {
    "row_number": 8,
    "col_number": 12,
    "well_radius": 7 / 2 * 1000,  # in micron,
    'length': 99.0 * 1000,  # in micron
    'width': 63.0 * 1000}  # in micron

@dataclass
class DishCalib_35mm(DishCalib):
    
    expected_radius: float = field(default_factory=float)
    expected_radius_upper: float = field(init=False)
    expected_radius_lower: float = field(init=False)
    
    def __post_init__(self)-> None:
        self.unpack_settings(SETTINGS_35MM)
        
        # Determine upper and lower bounds for the expected radius
        correction_percentage: float = 0.05 # decimal percentage
        self.expected_radius_upper = self.expected_radius + (self.expected_radius * correction_percentage)
        self.expected_radius_lower = self.expected_radius - (self.expected_radius * correction_percentage)
    
    def calibrate_dish(self, nikon: NikonTi2, list_points: list[tuple[float, float]] | None = None)-> dict:
        success_calibration = False    
        while success_calibration==False:
            # Define 3 points on the middle ring. The middle of the objective must be on the inner part of the ring
            point1, point2, point3 = self.get_edge_points(nikon, list_points)
            # Center of circle
            center, measured_radius = self.findCircle(point1,point2,point3)

            if not self.expected_radius_lower < measured_radius < self.expected_radius_upper:
                print(f"\nCalibration failed, start again! Radius={measured_radius} vs expected radius={self.expected_radius}")
                continue
            
            dish_measurments = {'A1': {'radius': measured_radius, 'center': center, 'ZDrive': None, 'PFSOffset': None}}
            
            success_calibration = True
        print(f"\nCalibration successful! Radius={measured_radius} vs expected radius={self.expected_radius}")
        return dish_measurments

    def get_edge_points(self, nikon: NikonTi2, list_points: list[tuple[float, float]] | None = None) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        if list_points is not None:
            if len(list_points) != 3:
                raise ValueError("List of points must have 3 points of tuple(float,float)")
            
            point1, point2, point3 = list_points
            return point1, point2, point3
        
        input("\nMove to the edge of the dish and press 'Enter'")
        point1 = nikon.get_stage_position()['xy']
        input("Move to another point of the edge of the dish and press 'Enter'")
        point2 = nikon.get_stage_position()['xy']
        input("Move to a final point of the edge of the dish and press 'Enter'")
        point3 = nikon.get_stage_position()['xy']
        return point1,point2,point3

# 
@dataclass
class DishCalib_96well(DishCalib):
    row_number: int = field(default_factory=int)
    col_number: int = field(default_factory=int)
    well_radius: float = field(default_factory=float)
    length: float = field(default_factory=float)  # in micron, from center A1 to center A12
    width: float = field(default_factory=float)  # in micron, from center A1 to center H1

    def __post_init__(self) -> None:
        self.unpack_settings(SETTINGS_96WELL)

    def calibrate_dish(self, nikon: NikonTi2, top_left_center: tuple[float,float] | None = None) -> dict:
        """Calculate the dish measurment of a 96-well plate. If the center of the top left corner of the dish is not provided, the user will be prompted to move to the top left corner of the dish. Else, the top left corner of the dish should be provided as x,y coordinates. Returns a dictionary with the well name as key and the center of the well as value."""
        
        
        x_tl, y_tl = self.get_center_point(nikon, top_left_center)

        # Create wells
        dish_measurments = {}
        for i, letter in enumerate(list(ascii_uppercase)[: self.row_number]):
            for j, numb in enumerate(range(1, self.col_number + 1)):
                x_center = x_tl - (self.length / (self.col_number - 1)) * j
                y_center = y_tl + (self.width / (self.row_number - 1)) * i
                
                dish_measurments[f"{letter}{numb}"] = {'radius':self.well_radius,'center':(x_center, y_center),'ZDrive':None,'PFSOffset':None}

        print(f"Calibration successful!")
        return dish_measurments

    def get_center_point(self, nikon, top_left_center):
        if top_left_center is None:
            # Define top left corner of dish
            input("Move to center of the A1 well of the dish and press 'Enter'")
            x_tl, y_tl = nikon.get_stage_position()["xy"]
        else:
            x_tl, y_tl = top_left_center
        return x_tl,y_tl