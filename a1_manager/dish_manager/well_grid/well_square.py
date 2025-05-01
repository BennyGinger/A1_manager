from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field

import numpy as np

from a1_manager.utils.utility_classes import StageCoord, WellSquareCoord
from a1_manager.dish_manager.well_grid_manager import WellGridManager


@dataclass
class WellSquareGrid(WellGridManager, dish_name=('ibidi-8well',)):
    y_tl: float = field(init=False)
    x_tl: float = field(init=False)
    y_br: float = field(init=False)
    x_br: float = field(init=False)
    well_width: float = field(init=False)
    well_length: float = field(init=False)
    
    def unpack_well_properties(self, well_measurments: WellSquareCoord, **kwargs)-> None: 
        """
        Unpack the well properties from the well measurements.
        Kwarg is not used in this subclass and can be ignored.
        """
        
        topleft = well_measurments.top_left
        bottomright = well_measurments.bottom_right
        self.y_tl, self.x_tl = topleft
        self.y_br, self.x_br = bottomright
        self.well_width = abs(self.y_br - self.y_tl)
        self.well_length = abs(self.x_br - self.x_tl)
    
    def generate_coordinates_per_axis(self, num_rects: tuple[int,int], align_correction: tuple[float,float])-> tuple[list,list]:
        """Get the list of center coordinates for each axis."""
        # Calculate the center position of the first and last rectangle
        y_start = self.y_tl + self.window_size[0] / 2 + align_correction[0]
        y_end = self.y_br - self.window_size[0] / 2 - align_correction[0]
        
        x_start = self.x_tl - align_correction[1] - self.window_size[1] / 2
        x_end = self.x_br + align_correction[1] + self.window_size[1] / 2
        
        # Get all coordinates between the start and stop position
        y_coords = np.linspace(y_start, y_end, int(num_rects[0])).tolist()
        x_coords = np.linspace(x_start, x_end, int(num_rects[1])).tolist()
        return y_coords, x_coords
    
    def update_well_grid(self, well_grid: dict[int, StageCoord], temp_point: StageCoord, count: int, x: float, y: float) -> int:
        """Update the well grid with the new rectangle center."""
        offset_x, offset_y = self.window_center_offset_um
        adjusted_x = x + offset_x
        adjusted_y = y - offset_y
        point = temp_point.copy()
        point['xy'] = (adjusted_x, adjusted_y)
        well_grid[count] = point
        return count + 1
