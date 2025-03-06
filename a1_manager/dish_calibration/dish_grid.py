from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from microscope_software.aquisition import Aquisition



#################### Grid classes ####################
@dataclass
class WellGrid():
    # Correction values to add to adjust the center position of dmd window to the full image size, in x and y axis respectively
    center_correction_pixel: list[int]
    center_adjust_um: tuple[float] = field(init=False)
    # x and y axis respectively
    rect_size: tuple[float] = field(init=False)
    # Overlap in x and y axis respectively
    overlaps: tuple[float,float] = field(init=False)
    # Maximum number of rectangles that can fit each axis, in x and y axis respectively
    numb_rectS: tuple[int,int] = field(init=False)
    # Correction values to add to align the body of rectangles on given axis, in x and y axis respectively
    align_correction: tuple[float,float] = field(init=False)
    
    def get_well_grid_instance(self, dish_name: str)-> 'WellGrid':
        # Dictionary mapping dish names to their corresponding classes
        dish_classes: dict[str, WellGrid] = {
            '35mm': WellGrid_circle,
            '96well': WellGrid_circle,
            'ibidi-8well': WellGrid_Ibidi}
        
        # Get the class based on dish_name
        dish_class = dish_classes.get(dish_name)
        if not dish_class:
            raise ValueError(f"Unknown dish name: {dish_name}")
        
        # Instantiate and return the appropriate subclass
        return dish_class(self.center_correction_pixel)
        
    def determine_rect_size(self, dmd_window_only: bool, aquisition: Aquisition)-> None:
        if dmd_window_only:
            dmd_size = aquisition.dmd.dmd_mask.dmd_size
            self.rect_size = (aquisition.size_pixel2micron(dmd_size[0]),aquisition.size_pixel2micron(dmd_size[1]))
        else:
            image_size = aquisition.camera.image_size
            self.rect_size = (int(aquisition.size_pixel2micron(image_size[0])),int(aquisition.size_pixel2micron(image_size[1])))
    
    def get_center_adjustment(self, dmd_window_only: bool, aquisition: Aquisition)-> None:
        if self.center_correction_pixel == [0,0]:
            self.center_adjust_um = (0,0)

        elif dmd_window_only:
            # Adjust the correction values to the binning in use
            center_correction_binned = tuple([int(corr//aquisition.camera.binning) for corr in self.center_correction_pixel])
            # Convert correction values to um
            self.center_adjust_um = tuple([aquisition.size_pixel2micron(corr) for corr in center_correction_binned])
        else:
            # For full image size, no correction is needed
            self.center_adjust_um = (0,0)
    
    def define_overlap(self, overlap: float | None)-> None:
        """Returns the optimum overlap for the given rectangle size,
        i.e. the overlap that will allow to fill a given axis with the maximum number of rectangles"""
        if overlap is not None:
            self.overlaps = (overlap,overlap)
            return None
        
        # If overlap is None, then determine optimum overlap
        rectS_in_y = (2*self.radius)/self.rect_size[1]
        rectS_in_x = (2*self.radius)/self.rect_size[0]
        
        ceiled_rectS_in_y = np.ceil(rectS_in_y)
        ceiled_rectS_in_x = np.ceil(rectS_in_x)
        overlap_y = (ceiled_rectS_in_y - rectS_in_y) / ceiled_rectS_in_y
        overlap_x = (ceiled_rectS_in_x - rectS_in_x) / ceiled_rectS_in_x
        self.overlaps = (overlap_x, overlap_y)
    
    def define_numb_of_rect_in_yNx(self)-> None:
        """Determine the maximum number of rectangles that can fit each axis, i.e. create a rectangular grid. X and Y axis depend on the dish type."""
        
        # Determine the axis lengths
        x_axis, y_axis = self.axis_length
        
        # Calculate the maximum number of rectangles side that can fit
        rectS_in_x = int(x_axis) // (self.rect_size[0] - self.rect_size[0] * self.overlaps[0])
        
        rectS_in_y = int(y_axis) // (self.rect_size[1] - self.rect_size[1] * self.overlaps[1])
        
        self.numb_rectS = (rectS_in_x, rectS_in_y)
    
    def align_rectangles_on_axis(self)-> None:
        """Correction factor to center the body of rectangles along the dish axis, i.e. the space between the tip of axis and first/last rectangle, if legnths of all rectangles is smaller than the length of the axis"""
        
        # Determine the axis lengths
        x_axis, y_axis = self.axis_length
        
        # Get the correction factor to center all rectangles along the dish axis
        corr_fact_y = (y_axis - (self.rect_size[1] - self.rect_size[1] * self.overlaps[1]) * self.numb_rectS[1]) / 2
        corr_fact_x = (x_axis - (self.rect_size[0] - self.rect_size[0] * self.overlaps[0]) * self.numb_rectS[0]) / 2
        self.align_correction = (corr_fact_x, corr_fact_y)
    
    @staticmethod
    def extract_focus_value(well_measurments):
        temp_point = {'xy':(None,None), 'ZDrive':None, 'PFSOffset':None}
        for k,v in well_measurments.items():
            if k in temp_point:
                temp_point[k] = v
        return temp_point
    
    @property
    def axis_length(self)-> tuple[float,float]:
        """Return the length of the x and y axis of the well, respectively"""
        if hasattr(self, 'radius'):
            return (2 * self.radius, 2 * self.radius)
        return (self.well_width, self.well_length)
    
    #################### Main method ####################
    def get_well_grid_coordinates(self, aquisition: Aquisition, well_measurments: dict, dmd_window_only: bool = True, overlap: float = None, **kwargs)-> dict:
        # Check if dmd is attached, if not, then dmd_window_only is False
        if not aquisition.is_dmd_attached:
            dmd_window_only = False
        
        # Extract dish and imaging properties
        self.unpack_well_properties(well_measurments, **kwargs)
        self.determine_rect_size(dmd_window_only, aquisition)
        self.get_center_adjustment(dmd_window_only, aquisition)
        
        # If overlap is None, then determine optimum overlap
        self.define_overlap(overlap)
        
        # Determine the maximum number of rectangles that can fit each axis, i.e. create a rectangular grid
        self.define_numb_of_rect_in_yNx()
        
        # Correction factor to center all rectangles along the dish axis
        self.align_rectangles_on_axis()
        
        # Get list of all coords of rectangle centers on each axis
        x_coord, y_coord = self.get_coord_list_per_axis()
        # Generate the list of rectangle
        well_grid = {}
        temp_point = self.extract_focus_value(well_measurments)
        count = 0
        for i,x in enumerate(x_coord):
            # To optimize the microscope path:
            if i%2==0: # if even, go from left to right
                for y in y_coord:
                    count = self.update_well_grid(well_grid, temp_point, count, x, y)
            else: # if odd, go from right to left
                for y in reversed(y_coord):
                    count = self.update_well_grid(well_grid, temp_point, count, x, y)
        return well_grid
    
    
    
@dataclass
class WellGrid_circle(WellGrid):
    radius: float = field(init=False)
    center: tuple[float,float] = field(init=False)
    n_corners_in: int = field(init=False)
    
    def unpack_well_properties(self, well_measurments: dict[str, dict[str, Any]], **kwargs)-> None:
        self.radius = well_measurments['radius']
        self.center = well_measurments['center']
        if kwargs:
            for k, v in kwargs.items():
                if k in ['n_corners_in']:
                    setattr(self, k, v)
        
    def get_coord_list_per_axis(self)-> tuple[list,list]:
        # Calculate the center position of the first and last rectangle
        first_x = self.center[0] - self.radius + self.align_correction[0] + self.rect_size[0]/2
        last_x = self.center[0] + self.radius - self.align_correction[0] - self.rect_size[0]/2
        
        first_y = self.center[1] + self.radius - self.align_correction[1] - self.rect_size[1]/2
        last_y = self.center[1] - self.radius + self.align_correction[1] + self.rect_size[1]/2
        
        # Get all coordinates between the start and stop position
        y_coord = np.linspace(first_y, last_y, int(self.numb_rectS[1]))
        x_coord = np.linspace(first_x, last_x, int(self.numb_rectS[0]))
        return x_coord, y_coord
    
    def update_well_grid(self, well_grid: dict, temp_point: dict, count: int, x: float, y: float) -> int:
        point = temp_point.copy()
        if self.is_rectangle_within_circle((x, y), self.n_corners_in):
            x = x + self.center_adjust_um[0]
            y = y - self.center_adjust_um[1]
            point['xy'] = (x,y)
            well_grid[count] = point
            count += 1
        return count
    
    def is_rectangle_within_circle(self, rect_coord: tuple[float, float], n_corner_in: int) -> bool:
        """ Check if the rectangle is within the circle: Allowing only n_corner corner to be outside the circle """
        x_center, y_center = rect_coord
        rect_width, rect_height = self.rect_size
        corner_in = 4
        
        # Get the 4 coords of the corners
        x_r = x_center - rect_width / 2
        y_t = y_center + rect_height / 2
        x_l = x_center + rect_width / 2
        y_b = y_center - rect_height / 2
        
        # Top left corner
        if self.is_point_outside_circle(x_l, y_t):
            corner_in -= 1
            if corner_in < n_corner_in:
                return False
        
        # Top right corner
        if self.is_point_outside_circle(x_r, y_t):
            corner_in -= 1
            if corner_in < n_corner_in:
                return False
        
        # Bottom left corner
        if self.is_point_outside_circle(x_l, y_b):
            corner_in -= 1
            if corner_in < n_corner_in:
                return False
        
        # Bottom right corner
        if self.is_point_outside_circle(x_r, y_b):
            corner_in -= 1
            if corner_in < n_corner_in:
                return False
        return True

    def is_point_outside_circle(self, point_x: float, point_y: float) -> bool:
        center_x, center_y = self.center
        distance_squared = (point_x - center_x) ** 2 + (point_y - center_y) ** 2
        return distance_squared > self.radius ** 2
 
    

@dataclass
class WellGrid_Ibidi(WellGrid):
    y_tl: float = field(init=False)
    x_tl: float = field(init=False)
    y_br: float = field(init=False)
    x_br: float = field(init=False)
    well_width: float = field(init=False)
    well_length: float = field(init=False)

    def unpack_well_properties(self, well_measurments: dict[str, tuple[tuple[float, float], tuple[float, float]]], **kwargs)-> None:  
        topleft, bottomright = well_measurments
        self.y_tl, self.x_tl = topleft
        self.y_br, self.x_br = bottomright
        self.well_width = abs(self.y_br - self.y_tl)
        self.well_length = abs(self.x_br - self.x_tl)
    
    def get_coord_list_per_axis(self)-> tuple[list,list]:
        # Calculate the center position of the first and last rectangle
        first_y = self.y_tl + self.rect_size[0] / 2 + self.align_correction[0]
        last_y = self.y_br - self.rect_size[0] / 2 - self.align_correction[0]
        
        first_x = self.x_tl - self.align_correction[1] - self.rect_size[1] / 2
        last_x = self.x_br + self.align_correction[1] + self.rect_size[1] / 2
        
        # Get all coordinates between the start and stop position
        y_coord = np.linspace(first_y, last_y, int(self.numb_rectS[0]))
        x_coord = np.linspace(first_x, last_x, int(self.numb_rectS[1]))
        return y_coord,x_coord
    
    def update_well_grid(self, well_grid: dict, temp_point: dict, count: int, x: float, y: float) -> int:
        point = temp_point.copy()
        x = x + self.center_adjust_um[0]
        y = y - self.center_adjust_um[1]
        point['xy'] = (x,y)
        well_grid[count] = point
        count += 1
        return count
    
    
    
