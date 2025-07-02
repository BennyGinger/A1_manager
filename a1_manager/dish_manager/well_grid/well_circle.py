from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field

import numpy as np

from a1_manager.utils.utility_classes import StageCoord, WellCircleCoord
from a1_manager.dish_manager.well_grid_manager import WellGridManager


@dataclass
class WellCircleGrid(WellGridManager):
    radius: float = field(init=False)
    center: tuple[float, float] = field(init=False) # xy respectively
    well_width: float = field(init=False)
    well_length: float = field(init=False)
    n_corners_in: int = field(init=False)
    
    def unpack_well_properties(self, well_measurments: WellCircleCoord, n_corners_in: int)-> None:
        """
        Unpack the well properties from the measurements.
        Kawrgs is used to pass the number of corners that need to be inside the circle.
        """
        
        self.radius = well_measurments['radius']
        self.center = well_measurments['center']
        self.n_corners_in = 4 if n_corners_in is None else n_corners_in
    
    def generate_coordinates_per_axis(self, num_rects: tuple[int,int], align_correction: tuple[float,float])-> tuple[list[float], list[float]]:
        """
        Compute the x and y coordinates for rectangle centers within the circular well.
        The x-coordinates span from the left boundary to the right boundary and the y-coordinates from the top boundary to the bottom boundary.
        """
        
        # Calculate the center position of the first and last rectangle
        x_start = self.center[0] - self.radius + align_correction[0] + self.window_size[0] / 2
        x_end = self.center[0] + self.radius - align_correction[0] - self.window_size[0] / 2
        
        y_start = self.center[1] + self.radius - align_correction[1] - self.window_size[1] / 2
        y_end = self.center[1] - self.radius + align_correction[1] + self.window_size[1] / 2
        
        # Get all coordinates between the start and stop position
        y_coords = np.linspace(y_start, y_end, int(num_rects[1])).tolist()
        x_coords = np.linspace(x_start, x_end, int(num_rects[0])).tolist()
        return x_coords, y_coords
    
    def update_well_grid(self, well_grid: dict[int, StageCoord], temp_point: StageCoord, count: int, x: float, y: float) -> int:
        """
        Update the well grid with a new rectangle center if it meets the criteria.
        The rectangle is only added if at least `n_corners_in` of its corners are within the circle.
        """
        
        if self._is_rectangle_within_circle((x, y), self.n_corners_in):
            offset_x, offset_y = self.window_center_offset_um
            adjusted_x = x + offset_x
            adjusted_y = y - offset_y
            point = temp_point.copy()
            point.xy = (adjusted_x, adjusted_y)
            well_grid[count] = point
            count += 1
        return count
    
    def _is_rectangle_within_circle(self, rect_coord: tuple[float, float], n_corner_in: int) -> bool:
        """
        Check if a rectangle (centered at rect_coord) is sufficiently inside the circle.
        The rectangle is considered acceptable if at least `n_corner_in` of its four corners are inside the circle.
        """
        
        x_center, y_center = rect_coord
        rect_width, rect_height = self.window_size
        corners = [
            (x_center + rect_width / 2, y_center + rect_height / 2), # top left
            (x_center - rect_width / 2, y_center + rect_height / 2), # top right
            (x_center + rect_width / 2, y_center - rect_height / 2), # bottom left
            (x_center - rect_width / 2, y_center - rect_height / 2)]  # bottom right
        
        # Count how many corners are inside the circle.
        inside_count = sum(1 for corner in corners if self._is_point_inside_circle(*corner))
        return inside_count >= n_corner_in
    
    def _is_point_inside_circle(self, point_x: float, point_y: float) -> bool:
        center_x, center_y = self.center
        distance_squared = (point_x - center_x) ** 2 + (point_y - center_y) ** 2
        return distance_squared < self.radius ** 2
