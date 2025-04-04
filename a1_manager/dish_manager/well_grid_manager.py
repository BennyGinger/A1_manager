from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Iterable, ClassVar

from dish_manager.dish_utils.geometry_utils import _randomise_fov
from utils.utils import load_config_file
from dish_manager.well_grid.grid_generator import GridBuilder
from utils.utility_classes import StageCoord, WellBaseCoord
from main import A1Manager


@dataclass
class WellGridManager(ABC):
    """Abstract-based class for managing the creating of well grid, consisting of rectangles that cover a well."""
    
    # Class variable. Dictionary mapping dish names to their corresponding classes
    _well_classes: ClassVar[dict[str, type[WellGridManager]]] = {}
    
    # Instance variables. All tuples are in xy axis respectively
    window_size: tuple[float, float] = field(init=False)
    window_center_offset_um: tuple[float, float] = field(init=False) 
    
    def __init_subclass__(cls, dish_name: str = None, **kwargs) -> None:
        """
        Automatically registers subclasses with a given dish_name.
        Meaning that the subclasses of WellGrid will automatically filled the _dish_classes dictionary.
        All the subclasses must have the dish_name attribute and are stored in the 'well_grid/' folder.
        """
        
        super().__init_subclass__(**kwargs)
        if dish_name:
            if isinstance(dish_name, str):
                dish_names = (dish_name,)
            for name in dish_names:
                WellGridManager._well_classes[name] = cls
    
    @classmethod
    def load_subclass_instance(cls, dish_name: str, dmd_window_only: bool, a1_manager: A1Manager) -> WellGridManager:
        """
        Factory method to obtain a well grid instance for a given dish.
        
        Args:
        - dish_name: Identifier of the dish (e.g., '35mm', '96well', 'ibidi-8well').
        - dmd_window_only: Whether to use or not the dmd window size to build the grid, Else, would use the full size window (which depends on the camera settings)
        - a1_manager: Class object that control the microscope.
        
        Returns:
            An instance of a WellGrid subclass corresponding to the dish.
        """
        
        # Get the class based on dish_name
        well_class = cls._well_classes.get(dish_name)
        if well_class is None:
            raise ValueError(f"Unknown dish name: {dish_name}")
        
        # Instantiate and return the appropriate subclass
        grid_instance = well_class()
        grid_instance._configure_grid_instance(a1_manager, dmd_window_only)
        return grid_instance
    
    def _configure_grid_instance(self, a1_manager: A1Manager, dmd_window_only: bool) -> None:
        """Extract the size of the window and adjust the center offset."""
        
        # Update the dmd window only flag
        if not a1_manager.is_dmd_attached:
            dmd_window_only = False
        
        # Set the size of the window
        self.window_size = a1_manager.window_size(dmd_window_only)
        
        # Adjust the center offset
        self._adjust_center_offset(a1_manager, dmd_window_only)

    def _adjust_center_offset(self, a1_manager: A1Manager, dmd_window_only: bool) -> None:
        """Adjust the center offset based on the dmd window."""
        
        # If no dmd window is used, the offset is zero
        if not dmd_window_only :
            self.window_center_offset_um = (0,0)
            return None
        
        # Get the fTurret to load the correct dmd_profile
        f_turret = a1_manager.core.get_property('FilterTurret1','Label')
        
        # Load the dmd profile
        dmd_profile = load_config_file('dmd_profile')
        if dmd_profile is None:
            raise FileNotFoundError("No dmd_profile file found. Please calibrate the dmd first.")
        
        # Get the correction values for the current dmd profile
        window_center_offset_pix: list[int] = dmd_profile[f_turret]["center_xy_corr_pix"]
        
        # Adjust the correction values to the binning in use
        binned = tuple([int(corr//a1_manager.camera.binning) for corr in window_center_offset_pix])
        
        # Convert correction values to um
        self.window_center_offset_um = tuple([a1_manager._size_pixel2micron(corr) for corr in binned])
    
    @property
    def axis_length(self)-> tuple[float,float]:
        """Return the length of the x and y axis of the well, respectively"""
        if hasattr(self, 'radius'):
            return (2 * self.radius, 2 * self.radius)
        return (self.well_width, self.well_length)
    
    @abstractmethod
    def _unpack_well_properties(self, well_measurements: dict, **kwargs) -> None:
        """Subclasses must implement this method to unpack well-specific properties."""
        pass
    
    @abstractmethod
    def _generate_coordinates_per_axis(self, num_rects: tuple[int,int], align_correction: tuple[float,float]) -> tuple[list,list]:
        """Subclasses must implement this method to compute the coordinates of the rectangles along each axis."""
        pass
    
    def _build_well_grid(self, x_coords: list[float], y_coords: list[float], temp_point: StageCoord) -> dict[int, StageCoord]:
        """Used by the child class to build the well grid based on the x and y coordinates."""
        
        well_grid: dict[int, StageCoord] = {}
        count: int = 0
        for i, x in enumerate(x_coords):
            # To optimise the movement of the stage, while taking images
            y_iterable: Iterable[float] = y_coords if i % 2 == 0 else list(reversed(y_coords))
            for y in y_iterable:
                count = self._update_well_grid(well_grid, temp_point, count, x, y)
        return well_grid
    
    @abstractmethod
    def _update_well_grid(self, well_grid: dict, temp_point: dict, count: int, x: float, y: float) -> int:
        """Subclasses must implement this method to update the well grid with the coordinates of the rectangles."""
        pass
    
    #################### Main method ####################
    def create_well_grid(self, well_measurements: WellBaseCoord, numb_field_view: int | None, overlap: float = None, n_corners_in: int=4) -> dict[int, StageCoord]:
        """
        Main method called by the child class.
        Create a grid of rectangles that covers the well.
        The rectangles are centered along the dish axis.
        The grid is optimized to minimize the number of rectangles and the overlap between them.
        If numb_field_view is not None, the grid is randomized to select a subset of the rectangles.
        Path of those randomised rectangles is optimised using TSP.
        
        Note: n_corners_in is only used for the 35mm and 96well dish. It will be ignored by the ibidi-8well dish.
        """
        
        # Extract dish and imaging properties
        self._unpack_well_properties(well_measurements, n_corners_in=n_corners_in)
        
        # Calculate the layout parameters for the grid
        grid_builder = GridBuilder()
        num_rects, align_correction = grid_builder.calculate_layout_parameters(self.window_size, self.axis_length, overlap)
        
        # Get list of all coords of rectangle centers on each axis
        x_coord, y_coord = self._generate_coordinates_per_axis(num_rects, align_correction)
        
        # Create an "empty" template point that contains the focus plane of the current well
        temp_point = well_measurements.get_template_point_coord()
        
        # Build the well grid
        well_grid = self._build_well_grid(x_coord, y_coord, temp_point)
        
        # Randomize the field of view if necessary
        if numb_field_view is None:
            return well_grid
        return _randomise_fov(well_grid, numb_field_view)
