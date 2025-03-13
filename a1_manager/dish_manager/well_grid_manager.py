from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Iterable, ClassVar

from dish_manager.dish_utils.geometry_utils import compute_optimal_overlap
from utils.utility_classes import StageCoord, WellBaseCoord
from main import A1Manager


@dataclass
class WellGridManager(ABC):
    """Abstract-based class for managing the creating of well grid, consisting of rectangles that cover a well."""
    
    # Class variable. Dictionary mapping dish names to their corresponding classes
    _well_classes: ClassVar[dict[str, type['WellGridManager']]] = {}
    # Instance variables. All tuples are in xy axis respectively
    dmd_window_only: bool = field(init=False)
    window_size: tuple[float, float] = field(init=False)
    window_center_offset_um: tuple[float, float] = field(init=False)
    overlaps: tuple[float,float] = field(init=False)
    num_rects: tuple[int,int] = field(init=False)
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
    def load_subclass_instance(cls, dish_name: str, window_center_offset_pix: list[int], dmd_window_only: bool, a1_manager: A1Manager)-> 'WellGridManager':
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
        grid_instance = well_class()
        grid_instance._configure_grid_instance(a1_manager, tuple(window_center_offset_pix), dmd_window_only)
        return grid_instance
        
    def _configure_grid_instance(self, a1_manager: A1Manager, window_center_offset_pix: tuple[int, int], dmd_window_only: bool)-> None:
        """Extract the size of the window and adjust the center offset."""
        
        # Add the dmd window only flag
        self._update_dmd_window_flag(a1_manager, dmd_window_only)
        
        # Determine the size of the window
        self._set_window_size(a1_manager)
        
        # Adjust the center offset
        self._adjust_center_offset(a1_manager, window_center_offset_pix)
    
    def _update_dmd_window_flag(self, a1_manager, dmd_window_only: bool)-> None:
        """Update the DMD window only flag."""
        
        if not a1_manager.is_dmd_attached:
            dmd_window_only = False
        self.dmd_window_only = dmd_window_only
    
    def _set_window_size(self, a1_manager: A1Manager)-> None:
        """Set the window size based on the DMD window only flag."""
        
        self.window_size = a1_manager.window_size(self.dmd_window_only)

    def _adjust_center_offset(self, a1_manager: A1Manager, window_center_offset_pix: tuple[int, int])-> None:
        """Adjust the center offset based on the DMD window only flag and convert the correction values to microns."""
        
        if not self.dmd_window_only or window_center_offset_pix == (0,0):
            self.window_center_offset_um = (0,0)

        else:
            # Adjust the correction values to the binning in use
            binned = tuple([int(corr//a1_manager.camera.binning) for corr in window_center_offset_pix])
            # Convert correction values to um
            self.window_center_offset_um = tuple([a1_manager.size_pixel2micron(corr) for corr in binned])
    
    @cached_property
    def axis_length(self)-> tuple[float,float]:
        """Return the length of the x and y axis of the well, respectively"""
        if hasattr(self, 'radius'):
            return (2 * self.radius, 2 * self.radius)
        return (self.well_width, self.well_length)
    
    @abstractmethod
    def _unpack_well_properties(self, well_measurements: dict, **kwargs) -> None:
        """Subclasses must implement this method to unpack well-specific properties."""
        pass
    
    def _define_overlap(self, overlap: float | None)-> None:
        """Sets the overlap between rectangles. If an overlap is provided, it is used; otherwise, computes an optimal value."""
        
        if overlap is not None:
            self.overlaps = (overlap, overlap)
        else:
            self.overlaps = compute_optimal_overlap(self.window_size, *self.axis_length)
    
    def _define_number_of_rectangles(self) -> None:
        """
        Determines the maximum number of rectangles that can fit along each axis.
        """
        x_axis, y_axis = self.axis_length
        num_x = int(x_axis) // int(self.rect_size[0] * (1 - self.overlaps[0]))
        num_y = int(y_axis) // int(self.rect_size[1] * (1 - self.overlaps[1]))
        self.num_rects = (num_x, num_y)
    
    def _align_rectangles_on_axis(self) -> None:
        """
        Computes the correction factors to center the grid along the x and y axes.
        """
        x_axis, y_axis = self.axis_length
        corr_x = (x_axis - (self.rect_size[0] * self.num_rects[0] * (1 - self.overlaps[0]))) / 2
        corr_y = (y_axis - (self.rect_size[1] * self.num_rects[1] * (1 - self.overlaps[1]))) / 2
        self.align_correction = (corr_x, corr_y)
    
    @abstractmethod
    def _generate_coordinates_per_axis(self) -> tuple[list,list]:
        """Subclasses must implement this method to compute the coordinates of the rectangles along each axis."""
        pass
    
    def _build_well_grid(self, x_coords: list[float], y_coords: list[float], temp_point: StageCoord) -> dict[int, StageCoord]:
        """Build the well grid based on the x and y coordinates."""
        
        well_grid: dict[int, StageCoord] = {}
        count: int = 0
        for i, x in enumerate(x_coords):
            y_iterable: Iterable[float] = y_coords if i % 2 == 0 else list(reversed(y_coords))
            for y in y_iterable:
                count = self._update_well_grid(well_grid, temp_point, count, x, y)
        return well_grid
    
    @abstractmethod
    def _update_well_grid(self, well_grid: dict, temp_point: dict, count: int, x: float, y: float) -> int:
        """Subclasses must implement this method to update the well grid with the coordinates of the rectangles."""
        pass
    
    #################### Main method ####################
    def create_well_grid(self, well_measurements: WellBaseCoord, overlap: float = None, **kwargs)-> dict[int, StageCoord]:
        """Create a grid of rectangles that covers the well. The rectangles are centered along the dish axis. The grid is optimized to minimize the number of rectangles and the overlap between them."""
        
        # Extract dish and imaging properties
        self._unpack_well_properties(well_measurements, **kwargs)
        
        # If overlap is None, then determine optimum overlap
        self._define_overlap(overlap)
        
        # Determine the maximum number of rectangles that can fit each axis, i.e. create a rectangular grid
        self._define_number_of_rectangles()
        
        # Correction factor to center all rectangles along the dish axis
        self._align_rectangles_on_axis()
        
        # Get list of all coords of rectangle centers on each axis
        x_coord, y_coord = self._generate_coordinates_per_axis()
        
        # Create an "empty" template point that contains the focus plane of the current well
        temp_point = well_measurements.get_template_point_coord()
        
        # Build the well grid
        return self._build_well_grid(x_coord, y_coord, temp_point)
    
    

    


    
    
    
