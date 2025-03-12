from dataclasses import dataclass, field

import numpy as np

from utils.class_utils import StageCoord
from dish_manager.well_grid_manager import WellGridManager
from dish_manager.dish_utils.well_utils import WellSquareCoord


@dataclass
class WellSquareGrid(WellGridManager, dish_name=('ibidi-8well',)):
    y_tl: float = field(init=False)
    x_tl: float = field(init=False)
    y_br: float = field(init=False)
    x_br: float = field(init=False)
    well_width: float = field(init=False)
    well_length: float = field(init=False)

    def unpack_well_properties(self, well_measurments: WellSquareCoord, **kwargs)-> None: 
        """Unpack the well properties from the well measurements."""
        topleft = well_measurments.top_left
        bottomright = well_measurments.bottom_right
        self.y_tl, self.x_tl = topleft
        self.y_br, self.x_br = bottomright
        self.well_width = abs(self.y_br - self.y_tl)
        self.well_length = abs(self.x_br - self.x_tl)
    
    def get_coord_list_per_axis(self)-> tuple[list,list]:
        """Get the list of center coordinates for each axis."""
        # Calculate the center position of the first and last rectangle
        first_y = self.y_tl + self.window_size[0] / 2 + self.align_correction[0]
        last_y = self.y_br - self.window_size[0] / 2 - self.align_correction[0]
        
        first_x = self.x_tl - self.align_correction[1] - self.window_size[1] / 2
        last_x = self.x_br + self.align_correction[1] + self.window_size[1] / 2
        
        # Get all coordinates between the start and stop position
        y_coord = np.linspace(first_y, last_y, int(self.numb_rectS[0]))
        x_coord = np.linspace(first_x, last_x, int(self.numb_rectS[1]))
        return y_coord,x_coord
    
    def update_well_grid(self, well_grid: dict, temp_point: StageCoord, count: int, x: float, y: float) -> int:
        """Update the well grid with the new rectangle center."""
        point = temp_point.copy()
        x = x + self.window_center_offset_um[0]
        y = y - self.window_center_offset_um[1]
        point['xy'] = (x,y)
        well_grid[count] = point
        count += 1
        return count
    