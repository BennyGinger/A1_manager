from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from a1_manager.main import A1Manager



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
        
    def determine_rect_size(self, dmd_window_only: bool, a1_manager: A1Manager)-> None:
        if dmd_window_only:
            dmd_size = a1_manager.dmd.dmd_mask.dmd_size
            self.rect_size = (a1_manager.size_pixel2micron(dmd_size[0]),a1_manager.size_pixel2micron(dmd_size[1]))
        else:
            image_size = a1_manager.camera.image_size
            self.rect_size = (int(a1_manager.size_pixel2micron(image_size[0])),int(a1_manager.size_pixel2micron(image_size[1])))
    
    def get_center_adjustment(self, dmd_window_only: bool, a1_manager: A1Manager)-> None:
        if self.center_correction_pixel == [0,0]:
            self.center_adjust_um = (0,0)

        elif dmd_window_only:
            # Adjust the correction values to the binning in use
            center_correction_binned = tuple([int(corr//a1_manager.camera.binning) for corr in self.center_correction_pixel])
            # Convert correction values to um
            self.center_adjust_um = tuple([a1_manager.size_pixel2micron(corr) for corr in center_correction_binned])
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
    def get_well_grid_coordinates(self, a1_manager: A1Manager, well_measurments: dict, dmd_window_only: bool = True, overlap: float = None, **kwargs)-> dict:
        # Check if dmd is attached, if not, then dmd_window_only is False
        if not a1_manager.is_dmd_attached:
            dmd_window_only = False
        
        # Extract dish and imaging properties
        self.unpack_well_properties(well_measurments, **kwargs)
        self.determine_rect_size(dmd_window_only, a1_manager)
        self.get_center_adjustment(dmd_window_only, a1_manager)
        
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

    


    
    
    
