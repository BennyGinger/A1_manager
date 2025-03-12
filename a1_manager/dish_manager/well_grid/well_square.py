from dataclasses import dataclass, field

import numpy as np

from dish_manager.well_grid_manager import WellGrid


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