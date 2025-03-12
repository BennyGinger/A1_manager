from dataclasses import dataclass, field
from string import ascii_uppercase

from microscope_hardware.nikon import NikonTi2
from a1_manager.dish_manager.dish_calib_manager import DishCalibManager
from dish_manager.dish_calibration.prompt_utils import prompt_for_center
from dish_manager.dish_calibration.well_utils import WellSquare


SETTINGS_IBIDI = {'row_number': 2,
                  'col_number': 4,
                  'length': 48 * 1000, # in micron
                  'width': 21 * 1000, # in micron
                  'well_length': 11 * 1000, # in micron
                  'well_width': 10 * 1000, # in micron
                  'well_gap_length': (1.4 * 1000, 2 * 1000, 1.4 * 1000), # first, second and third gap respectively, in micron
                  'well_gap_width': 1.6 *1000} # in micron

@dataclass
class DishIbidi(DishCalibManager, dish_name='ibidi-8well'):
    
    row_number: int = field(default_factory=int)
    col_number: int = field(default_factory=int)
    length: float = field(default_factory=float) # x-axis
    width: float = field(default_factory=float) # y-axis
    well_length: float = field(default_factory=float)
    well_width: float = field(default_factory=float)
    well_gap_length: tuple[float, float, float] = field(default_factory=tuple)
    well_gap_width: float = field(default_factory=float)

    def __post_init__(self)-> None:
        self.unpack_settings(SETTINGS_IBIDI)
        
    def calibrate_dish(self, nikon: 'NikonTi2')-> dict[str, 'WellSquare']:
        """Calibrates the Ibidi dish by computing the coordinates for each well.
        
        Prompts the user to move the objective to the center of well A1.
        
        Args:
            nikon: An instance of NikonTi2 that control the microscope.
        
        Returns:
            A dictionary mapping well names (e.g., 'A1') and their coordinates (top-left and bottom-right corners)."""
            
        # Prompt the user to move the stage to the center of the A1 well
        x_center, y_center = prompt_for_center(nikon)
        
        # Calculate the top-left and bottom-right corners for well A1.
        x_tl = x_center + self.well_length / 2
        y_tl = y_center - self.well_width / 2
        x_br = x_center - self.well_length / 2
        y_br = y_center + self.well_width / 2
        
        # Create wells
        dish_measurements: dict[str, WellSquare] = {}
        for i, letter in enumerate(ascii_uppercase[:self.row_number]):
            for j in range(self.col_number):
                well_number = j + 1
                # Compute the total gap length for the current column (if any).
                gap_sum = sum(self.well_gap_length[:j]) if j > 0 else 0
                
                well_x_tl = x_tl - self.well_length * j - gap_sum
                well_y_tl = y_tl + (self.well_width + self.well_gap_width) * i
                well_x_br = x_br - self.well_length * j - gap_sum
                well_y_br = y_br + (self.well_width + self.well_gap_width) * i
                # Save the well
                dish_measurements[f"{letter}{well_number}"] = WellSquare(top_left=(well_x_tl, well_y_tl), 
                                                                         bottom_right=(well_x_br, well_y_br))
        return dish_measurements