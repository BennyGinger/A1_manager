from dataclasses import dataclass, field
from string import ascii_uppercase

from microscope_hardware.nikon import NikonTi2
from dish_manager.dish_calib import DishCalib


SETTINGS_IBIDI = {'row_number': 2,
                  'col_number': 4,
                  'length': 48 * 1000, # in micron
                  'width': 21 * 1000, # in micron
                  'well_length': 11 * 1000, # in micron
                  'well_width': 10 * 1000, # in micron
                  'well_gap_length': (1.4 * 1000, 2 * 1000, 1.4 * 1000), # first, second and third gap respectively, in micron
                  'well_gap_width': 1.6 *1000} # in micron

@dataclass
class DishCalib_Ibidi(DishCalib):
    
    row_number: int = field(default_factory=int)
    col_number: int = field(default_factory=int)
    length: float = field(default_factory=float) # x-axis
    width: float = field(default_factory=float) # y-axis
    well_length: float = field(default_factory=float)
    well_width: float = field(default_factory=float)
    well_gap_length: tuple[float, float, float] = field(default_factory=tuple)
    well_gap_width: float = field(default_factory=float)

    def __post_init__(self):
        self.unpack_settings(SETTINGS_IBIDI)
        
    def calibrate_dish(self, nikon: NikonTi2)-> dict:
        # Define top left corner of dish
        input("Move the center of the objective to the center of the well A1 and press 'Enter'")
        x_center, y_center = nikon.get_stage_position()['xy']
        
        # Get top left and bottom right corner of the first well
        x_tl = x_center + self.well_length / 2
        y_tl = y_center - self.well_width / 2
        x_br = x_center - self.well_length / 2
        y_br = y_center + self.well_width / 2
        
        # Create wells
        dish_measurments = {}
        for i,letter in enumerate(list(ascii_uppercase)[:self.row_number]):
            for j,numb in enumerate(range(1,self.col_number+1)):
                # Calculate the top left and bottom right corner of the well
                
                well_x_tl = x_tl - self.well_length * j - sum(self.well_gap_length[:j])
                well_y_tl = y_tl + (self.well_width + self.well_gap_width) * i
                well_x_br = x_br - self.well_length * j - sum(self.well_gap_length[:j])
                well_y_br = y_br + (self.well_width + self.well_gap_width) * i
                # Save the well
                dish_measurments[f"{letter}{numb}"] = [(well_x_tl, well_y_tl),(well_x_br, well_y_br)]
        
        print(f"Calibration successful!")   
        return dish_measurments