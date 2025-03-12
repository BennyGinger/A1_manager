from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import numpy as np

from dish_manager.dish_utils.geometry_utils import compute_optimal_overlap
from main import A1Manager


@dataclass
class WellGridManager(ABC):
    # Dictionary mapping dish names to their corresponding classes
    _well_classes: dict[str, type['WellGridManager']] = {}
    dmd_window_only: bool = field(init=False)
    window_size: tuple[float, float] = field(init=False) # xy axis respectively
    # Offsets values to add to adjust the center position of dmd window to the full image size, in x and y axis respectively
    window_center_offset_um: tuple[float, float] = field(init=False)
    
    
    
    # Overlap in x and y axis respectively
    overlaps: tuple[float,float] = field(init=False)
    # Maximum number of rectangles that can fit each axis, in x and y axis respectively
    numb_rectS: tuple[int,int] = field(init=False)
    # Correction values to add to align the body of rectangles on given axis, in x and y axis respectively
    align_correction: tuple[float,float] = field(init=False)
    
    def __init_subclass__(cls, dish_name: str = None, **kwargs) -> None:
        """Automatically registers subclasses with a given dish_name. Meaning that the subclasses of WellGrid will automatically filled the _dish_classes dictionary. All the subclasses must have the dish_name attribute and are stored in the 'well_grid/' folder."""
        
        super().__init_subclass__(**kwargs)
        if dish_name:
            if isinstance(dish_name, str):
                dish_names = (dish_name,)
            for name in dish_names:
                WellGridManager._well_classes[name] = cls
    
    @classmethod
    def get_well_grid_instance(cls, dish_name: str, center_correction_pixel: list[int], dmd_window_only: bool, a1_manager: A1Manager)-> 'WellGridManager':
        """Factory method to obtain a well grid instance for a given dish.
        
        Args:
            dish_name: Identifier of the dish (e.g., '35mm', '96well', 'ibidi-8well').
            center_correction_pixel: Correction values to be used by the grid.
        
        Returns:
            An instance of a WellGrid subclass corresponding to the dish."""
            
        # Get the class based on dish_name
        well_class = cls._well_classes.get(dish_name)
        if well_class is None:
            raise ValueError(f"Unknown dish name: {dish_name}")
        
        # Instantiate and return the appropriate subclass
        well_grid = well_class(window_center_offset_pix=tuple(center_correction_pixel),
                          dmd_window_only=dmd_window_only)
        well_grid.configure(a1_manager)
        return well_grid
        
    def configure(self, a1_manager: A1Manager, window_center_offset_pix: tuple[int, int])-> None:
        """Extract the size of the window and adjust the center offset."""
        
        self.window_size = a1_manager.window_size(self.dmd_window_only)
        self._adjust_center_offset(a1_manager, window_center_offset_pix)
    
    @abstractmethod
    def unpack_well_properties(self, well_measurements: dict, **kwargs) -> None:
        """Subclasses must implement this method to unpack well-specific properties."""
        pass
    
    def _adjust_center_offset(self, a1_manager: A1Manager, window_center_offset_pix: tuple[int, int])-> None:
        if not self.dmd_window_only or window_center_offset_pix == (0,0):
            self.window_center_offset_um = (0,0)

        else:
            # Adjust the correction values to the binning in use
            binned = tuple([int(corr//a1_manager.camera.binning) for corr in window_center_offset_pix])
            # Convert correction values to um
            self.window_center_offset_um = tuple([a1_manager.size_pixel2micron(corr) for corr in binned])
    
    def define_overlap(self, overlap: float | None)-> None:
        """Sets the overlap between rectangles. If an overlap is provided, it is used; otherwise, computes an optimal value."""
        
        if overlap is not None:
            self.overlaps = (overlap, overlap)
        else:
            self.overlaps = compute_optimal_overlap(self.window_size, self.well_width, self.well_length)
    
    
    
    
    
    
    def define_numb_of_rect_in_yNx(self)-> None:
        """Determine the maximum number of rectangles that can fit each axis, i.e. create a rectangular grid. X and Y axis depend on the dish type."""
        
        # Determine the axis lengths
        x_axis, y_axis = self.axis_length
        
        # Calculate the maximum number of rectangles side that can fit
        rectS_in_x = int(x_axis) // (self.window_size[0] - self.window_size[0] * self.overlaps[0])
        
        rectS_in_y = int(y_axis) // (self.window_size[1] - self.window_size[1] * self.overlaps[1])
        
        self.numb_rectS = (rectS_in_x, rectS_in_y)
    
    def align_rectangles_on_axis(self)-> None:
        """Correction factor to center the body of rectangles along the dish axis, i.e. the space between the tip of axis and first/last rectangle, if legnths of all rectangles is smaller than the length of the axis"""
        
        # Determine the axis lengths
        x_axis, y_axis = self.axis_length
        
        # Get the correction factor to center all rectangles along the dish axis
        corr_fact_y = (y_axis - (self.window_size[1] - self.window_size[1] * self.overlaps[1]) * self.numb_rectS[1]) / 2
        corr_fact_x = (x_axis - (self.window_size[0] - self.window_size[0] * self.overlaps[0]) * self.numb_rectS[0]) / 2
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
        self.window_size = a1_manager.window_size
        self._adjust_center_offset(dmd_window_only, a1_manager)
        
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

    


    
    
    
