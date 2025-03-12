from dataclasses import dataclass, field
from typing import Any

import numpy as np

from dish_manager.well_grid_manager import WellGrid


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
 