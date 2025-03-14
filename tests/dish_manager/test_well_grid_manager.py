from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Iterable, ClassVar

# Dummy implementation for compute_optimal_overlap.
def compute_optimal_overlap(window_size: tuple[float, float], axis_x: float, axis_y: float) -> tuple[float, float]:
    return (0.1, 0.1)

# Dummy A1Manager and its camera.
class DummyCamera:
    def __init__(self):
        self.binning = 2

class DummyA1Manager:
    def __init__(self):
        self.camera = DummyCamera()
    def window_size(self, dmd_window_only: bool) -> tuple[float, float]:
        # For testing, return a different window size if dmd_window_only is True.
        return (50.0, 50.0) if dmd_window_only else (100.0, 200.0)
    def size_pixel2micron(self, pixel_value: int) -> float:
        # Simple 1:1 conversion for testing.
        return float(pixel_value)
    @property
    def is_dmd_attached(self) -> bool:
        return True

# Dummy WellBaseCoord.
class DummyWellBaseCoord:
    def get_template_point_coord(self) -> dict:
        # Template point with a dummy focus plane.
        return {'xy': (0, 0), 'z': 0}

# We'll use a dict as our StageCoord.
StageCoord = dict

# The abstract base class from your final version.
@dataclass
class WellGridManager(ABC):
    """Abstract-based class for managing the creating of well grid, consisting of rectangles that cover a well."""
    
    _well_classes: ClassVar[dict[str, type['WellGridManager']]] = {}
    
    dmd_window_only: bool = field(init=False)
    # All tuples are in xy axis respectively.
    window_size: tuple[float, float] = field(init=False)
    window_center_offset_um: tuple[float, float] = field(init=False)
    overlaps: tuple[float, float] = field(init=False)
    num_rects: tuple[int, int] = field(init=False)
    align_correction: tuple[float, float] = field(init=False)
    
    def __init_subclass__(cls, dish_name: str = None, **kwargs) -> None:
        """Automatically registers subclasses with a given dish_name."""
        super().__init_subclass__(**kwargs)
        if dish_name:
            if isinstance(dish_name, str):
                dish_names = (dish_name,)
            for name in dish_names:
                WellGridManager._well_classes[name] = cls
    
    @classmethod
    def load_subclass_instance(cls, dish_name: str, window_center_offset_pix: list[int],
                               dmd_window_only: bool, a1_manager: DummyA1Manager) -> 'WellGridManager':
        """Factory method to obtain a well grid instance for a given dish."""
        well_class = cls._well_classes.get(dish_name)
        if well_class is None:
            raise ValueError(f"Unknown dish name: {dish_name}")
        
        grid_instance = well_class()
        grid_instance._configure_grid_instance(a1_manager, tuple(window_center_offset_pix), dmd_window_only)
        return grid_instance
        
    def _configure_grid_instance(self, a1_manager: DummyA1Manager, window_center_offset_pix: tuple[int, int],
                                 dmd_window_only: bool) -> None:
        """Extract the size of the window and adjust the center offset."""
        self._update_dmd_window_flag(a1_manager, dmd_window_only)
        self._set_window_size(a1_manager)
        self._adjust_center_offset(a1_manager, window_center_offset_pix)
    
    def _update_dmd_window_flag(self, a1_manager: DummyA1Manager, dmd_window_only: bool) -> None:
        """Update the DMD window only flag."""
        if not a1_manager.is_dmd_attached:
            dmd_window_only = False
        self.dmd_window_only = dmd_window_only
    
    def _set_window_size(self, a1_manager: DummyA1Manager) -> None:
        """Set the window size based on the DMD window only flag."""
        self.window_size = a1_manager.window_size(self.dmd_window_only)

    def _adjust_center_offset(self, a1_manager: DummyA1Manager, window_center_offset_pix: tuple[int, int]) -> None:
        """Adjust the center offset based on the DMD window only flag and convert the correction values to microns."""
        if not self.dmd_window_only or window_center_offset_pix == (0, 0):
            self.window_center_offset_um = (0, 0)
        else:
            # Adjust the correction values to the binning in use.
            binned = tuple(int(corr // a1_manager.camera.binning) for corr in window_center_offset_pix)
            # Convert correction values to um.
            self.window_center_offset_um = tuple(a1_manager.size_pixel2micron(corr) for corr in binned)
    
    @cached_property
    def axis_length(self) -> tuple[float, float]:
        """Return the length of the x and y axis of the well, respectively."""
        if hasattr(self, 'radius'):
            return (2 * self.radius, 2 * self.radius)
        return (self.well_width, self.well_length)
    
    @abstractmethod
    def _unpack_well_properties(self, well_measurements: dict, **kwargs) -> None:
        """Subclasses must implement this method to unpack well-specific properties."""
        pass
    
    def _define_overlap(self, overlap: float | None) -> None:
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
    def _generate_coordinates_per_axis(self) -> tuple[list, list]:
        """Subclasses must implement this method to compute the coordinates of the rectangles along each axis."""
        pass
    
    def _build_well_grid(self, x_coords: list[float], y_coords: list[float],
                         temp_point: StageCoord) -> dict[int, StageCoord]:
        """Build the well grid based on the x and y coordinates."""
        well_grid: dict[int, StageCoord] = {}
        count: int = 0
        for i, x in enumerate(x_coords):
            y_iterable: Iterable[float] = y_coords if i % 2 == 0 else list(reversed(y_coords))
            for y in y_iterable:
                count = self._update_well_grid(well_grid, temp_point, count, x, y)
        return well_grid
    
    @abstractmethod
    def _update_well_grid(self, well_grid: dict, temp_point: dict, count: int,
                          x: float, y: float) -> int:
        """Subclasses must implement this method to update the well grid with the coordinates of the rectangles."""
        pass
    
    def create_well_grid(self, well_measurements: DummyWellBaseCoord, overlap: float = None,
                         **kwargs) -> dict[int, StageCoord]:
        """Create a grid of rectangles that covers the well."""
        self._unpack_well_properties(well_measurements.__dict__, **kwargs)
        self._define_overlap(overlap)
        self._define_number_of_rectangles()
        self._align_rectangles_on_axis()
        x_coord, y_coord = self._generate_coordinates_per_axis()
        temp_point = well_measurements.get_template_point_coord()
        return self._build_well_grid(x_coord, y_coord, temp_point)

# Create a dummy concrete subclass for testing.
class DummyWellGridManager(WellGridManager, dish_name="dummy"):
    def _unpack_well_properties(self, well_measurements: dict, **kwargs) -> None:
        # For testing, set dummy values.
        self.well_width = 100.0
        self.well_length = 200.0
        self.rect_size = (10, 20)
    
    def _generate_coordinates_per_axis(self) -> tuple[list, list]:
        # For testing, return fixed x and y coordinates.
        return ([0, 10, 20], [0, 5])
    
    def _update_well_grid(self, well_grid: dict, temp_point: dict, count: int,
                          x: float, y: float) -> int:
        # Update the well grid using the provided point template.
        point = temp_point.copy()
        x_adj = x + self.window_center_offset_um[0]
        y_adj = y - self.window_center_offset_um[1]
        point['xy'] = (x_adj, y_adj)
        well_grid[count] = point
        return count + 1

# --------------------- Pytest Tests ---------------------

def test_load_subclass_instance():
    a1_manager = DummyA1Manager()
    # Provide a nonzero offset; with binning=2, offset [4, 6] becomes (2, 3)
    grid_instance = WellGridManager.load_subclass_instance("dummy", [4, 6], True, a1_manager)
    assert isinstance(grid_instance, DummyWellGridManager)
    assert grid_instance.dmd_window_only is True
    # Check that window_size reflects dmd_window_only True.
    assert grid_instance.window_size == a1_manager.window_size(True)
    # Check that the center offset is updated correctly.
    assert grid_instance.window_center_offset_um == (2.0, 3.0)

def test_create_well_grid():
    a1_manager = DummyA1Manager()
    dummy_coord = DummyWellBaseCoord()
    grid_instance = DummyWellGridManager()
    grid_instance._configure_grid_instance(a1_manager, (4, 6), True)
    grid = grid_instance.create_well_grid(dummy_coord)
    # With _generate_coordinates_per_axis returning 3 x-coords and 2 y-coords, expect 6 grid points.
    assert len(grid) == 6
    # Ensure the keys are sequential: 0, 1, 2, 3, 4, 5.
    assert sorted(grid.keys()) == list(range(6))
    # For the first row (x=0) with offset (2.0, 3.0): expected points:
    # (0+2.0, 0-3.0) -> (2.0, -3.0) and (0+2.0, 5-3.0) -> (2.0, 2.0).
    assert grid[0]['xy'] == (2.0, -3.0)
    assert grid[1]['xy'] == (2.0, 2.0)

def test_zigzag_pattern():
    # Test the zigzag (serpentine) pattern in _build_well_grid.
    a1_manager = DummyA1Manager()
    dummy_coord = DummyWellBaseCoord()
    grid_instance = DummyWellGridManager()
    # Use zero offset for simplicity.
    grid_instance._configure_grid_instance(a1_manager, (0, 0), True)
    # Override _generate_coordinates_per_axis to control the coordinates.
    def custom_generate_coords():
        return ([1, 2], [10, 20, 30])
    grid_instance._generate_coordinates_per_axis = custom_generate_coords
    grid = grid_instance.create_well_grid(dummy_coord)
    # For first x (i=0): use y-order [10, 20, 30].
    # For second x (i=1): use reversed y-order [30, 20, 10].
    expected_order = [
        (1, 10), (1, 20), (1, 30),
        (2, 30), (2, 20), (2, 10)
    ]
    # Extract the 'xy' coordinates from the grid.
    actual_order = [grid[i]['xy'] for i in range(len(grid))]
    assert actual_order == expected_order
