from __future__ import annotations
from dataclasses import dataclass, field
from string import ascii_uppercase
from pathlib import Path

import numpy as np

from microscope_hardware.nikon import NikonTi2
from utils.utils import between


SETTINGS_IBIDI = {'row_number': 2,
                  'col_number': 4,
                  'length': 48 * 1000, # in micron
                  'width': 21 * 1000, # in micron
                  'well_length': 11 * 1000, # in micron
                  'well_width': 10 * 1000, # in micron
                  'well_gap_length': (1.4 * 1000, 2 * 1000, 1.4 * 1000), # first, second and third gap respectively, in micron
                  'well_gap_width': 1.6 *1000} # in micron

SETTINGS_35MM = {'expected_radius': 10.5 * 1000} # in micron

SETTINGS_96WELL = {
    "row_number": 8,
    "col_number": 12,
    "well_radius": 7 / 2 * 1000,  # in micron,
    'length': 99.0 * 1000,  # in micron
    'width': 63.0 * 1000  # in micron
}

@dataclass
class DishCalib():
    
    def get_dish_calib_instance(self, dish_name: str) -> 'DishCalib':
        # Dictionary mapping dish names to their corresponding classes
        dish_classes: dict[str, DishCalib] = {
            '35mm': DishCalib_35mm,
            '96well': DishCalib_96well,
            'ibidi-8well': DishCalib_Ibidi}

        # Get the class based on dish_name
        dish_class = dish_classes.get(dish_name)
        if not dish_class:
            raise ValueError(f"Unknown dish name: {dish_name}")

        # Instantiate and return the appropriate subclass
        return dish_class()
    
    def unpack_settings(self, settings: dict) -> None:
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @staticmethod
    def findCircle(point1: tuple[int, int], point2: tuple[int, int], point3: tuple[int, int]) -> tuple[tuple[float,float], float]:
        """Considering that (x - xc)^2 + (y - yc)^2 = r^2 and that all 3 points are on the circle,
        we can have a general eqn x^2 + y^2 - 2*xc*x - 2*yc*y + c = 0."""

        x1, y1 = point1
        x2, y2 = point2
        x3, y3 = point3

        x12 = x1 - x2
        x13 = x1 - x3
        y12 = y1 - y2
        y13 = y1 - y3
        y31 = y3 - y1
        y21 = y2 - y1
        x31 = x3 - x1
        x21 = x2 - x1

        sqx13 = x1 * x1 - x3 * x3
        sqy13 = y1 * y1 - y3 * y3
        sqx21 = x2 * x2 - x1 * x1
        sqy21 = y2 * y2 - y1 * y1

        yc = (sqx13 * x12 + sqy13 * x12 + sqx21 * x13 + sqy21 * x13) // (2 * (y31 * x12 - y21 * x13))

        xc = (sqx13 * y12 + sqy13 * y12 + sqx21 * y13 + sqy21 * y13) // (2 * (x31 * y12 - x21 * y13))

        c = -(x1 * x1) - y1 * y1 - 2 * xc * x1 - 2 * yc * y1

        # eqn of circle be x^2 + y^2 + 2*g*x + 2*f*y + c = 0
        # where centre is (h = -g, k = -f)
        center = (-xc, -yc)
        # radius r as r^2 = x^2 + y^2 - c
        radius = round(np.sqrt((xc ** 2) + (yc ** 2) - c), 5)
        return center, radius

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

            if not between(measured_radius, self.expected_radius_lower, self.expected_radius_upper):
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

@dataclass
class DishCalib_Ibidi(DishCalib):
    
    row_number: int = field(default_factory=int)
    col_number: int = field(default_factory=int)
    length: float = field(default_factory=float) # x-axis
    width: float = field(default_factory=float) # y-axis
    well_length: float = field(default_factory=float)
    well_width: float = field(default_factory=float)
    well_gap_length: tuple[float, float, float] = field(default_factory=tuple)
    well_gap_width: float = field(default_factory=float)

    def __post_init__(self):
        self.unpack_settings(SETTINGS_IBIDI)
        
    def calibrate_dish(self, nikon: NikonTi2)-> dict:
        # Define top left corner of dish
        input("Move the center of the objective to the center of the well A1 and press 'Enter'")
        x_center, y_center = nikon.get_stage_position()['xy']
        
        # Get top left and bottom right corner of the first well
        x_tl = x_center + self.well_length / 2
        y_tl = y_center - self.well_width / 2
        x_br = x_center - self.well_length / 2
        y_br = y_center + self.well_width / 2
        
        # Create wells
        dish_measurments = {}
        for i,letter in enumerate(list(ascii_uppercase)[:self.row_number]):
            for j,numb in enumerate(range(1,self.col_number+1)):
                # Calculate the top left and bottom right corner of the well
                
                well_x_tl = x_tl - self.well_length * j - sum(self.well_gap_length[:j])
                well_y_tl = y_tl + (self.well_width + self.well_gap_width) * i
                well_x_br = x_br - self.well_length * j - sum(self.well_gap_length[:j])
                well_y_br = y_br + (self.well_width + self.well_gap_width) * i
                # Save the well
                dish_measurments[f"{letter}{numb}"] = [(well_x_tl, well_y_tl),(well_x_br, well_y_br)]
        
        print(f"Calibration successful!")   
        return dish_measurments
  



if __name__ == "__main__":
    from a1_pipeline.microscope_software.aquisition import Aquisition
    import json
    
    settings = {'aquisition_settings':{'exposure_ms':300,
                           'binning':2,
                           'objective':'20x', # Only 10x or 20x are calibrated for now
                           'lamp_name':'pE-800',  # 'pE-800','pE-4000','DiaLamp'
                           'focus_device':'ZDrive'},
    
    'preset_seg':{'optical_configuration':'GFP', # Channel to seg for analysis
                  'intensity':15}} # 0-100% 
    
    
    aquisition = Aquisition(**settings['aquisition_settings'])
    aquisition.oc_settings(**settings['preset_seg'])
    
    
    def get_calib(dish_name: str):
        if dish_name == '35mm':
            dish = DishCalib_35mm()
            data = dish.calibrate_dish(aquisition.nikon)    
        elif dish_name == '96well':
            dish = DishCalib_96well()
            data = dish.calibrate_dish(aquisition.nikon)
        elif dish_name == 'ibidi-8well':
            dish = DishCalib_Ibidi()
            data = dish.calibrate_dish(aquisition.nikon)
    
        with open('dish_measurements.json', 'w') as f:
            json.dump(data, f)
    
    def load_calib():
        with open('dish_measurements.json', 'r') as f:
            data = json.load(f)
        return data
    
    dish_name = 'ibidi-8well'
    
    # data = get_calib(dish_name)
    data = load_calib()
    
    def get_center_point(dish_name: str, data: dict, well: str):
        if dish_name == 'ibidi-8well':
            tl, br = data[well]
            
            cx = (tl[0] + br[0]) / 2
            cy = (tl[1] + br[1]) / 2
            print(f"Center of well {well}: {cx},{cy}")
            return {'xy':(cx,cy),'ZDrive': 2580}
        
        return {'xy': data[well]['center'],'ZDrive': 2580}
        
    # Calculate the center of the well
    point = get_center_point(dish_name, data, 'B4')
    print(point)
    aquisition.nikon.set_stage_position(point)
    
    