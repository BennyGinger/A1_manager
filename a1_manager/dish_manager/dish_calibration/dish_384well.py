from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
from string import ascii_uppercase
import logging

from a1_manager import CONFIG_DIR
from a1_manager.microscope_hardware.nikon import NikonTi2
from a1_manager.dish_manager.dish_calib_manager import DishCalibManager
from a1_manager.utils.utility_classes import WellSquareCoord
from a1_manager.utils.json_utils import load_config_file, save_config_file
from a1_manager.dish_manager.dish_utils.prompt_utils import prompt_for_top_left_A1, prompt_for_top_left_P24


SETTINGS_384WELL = {
    'row_number': 16,
    'col_number': 24,
    'length': 127.76 * 1000, # in micron
    'width': 85.48 * 1000, # in micron
    'well_length': 2.8 * 1000, # in micron
    'well_width': 2.8 * 1000, # in micron
    'well_gap_length': 1.7 * 1000, # in micron
    'well_gap_width': 1.7 *1000 # in micron
    }

@dataclass
class Dish384Well(DishCalibManager):
    """
    Calibration handler for the 384-well plate.
    
    Attributes:
    - row_number (int): Number of rows in the dish.
    - col_number (int): Number of columns in the dish.
    - length (float): Length of the dish along the x-axis (in microns).
    - width (float): Width of the dish along the y-axis (in microns).
    - well_length (float): Length of a well (in microns).
    - well_width (float): Width of a well (in microns).
    - well_gap_length (tuple[float, float, float]): Length of the gaps between wells (in microns).
    - well_gap_width (float): Width of the gaps between wells (in microns).
    """
    
    
    row_number: int = field(default_factory=int)
    col_number: int = field(default_factory=int)
    length: float = field(default_factory=float) # x-axis
    width: float = field(default_factory=float) # y-axis
    well_length: float = field(default_factory=float)
    well_width: float = field(default_factory=float)
    well_gap_length: float = field(default_factory=float)
    well_gap_width: float = field(default_factory=float)

    def __post_init__(self)-> None:
        self.unpack_settings(SETTINGS_384WELL)
        
            
    def _calibrate_dish(self, nikon: NikonTi2) -> dict[str, WellSquareCoord]:  # type: ignore[override]
        """
        Try to load the calibration template for the 384-well plate from the config directory. 
        If not found, perform manual calibration.
        """
        calib_name = f"calib_384well.json"
        calib_temp_path = CONFIG_DIR.joinpath(calib_name)
        if calib_temp_path.exists():
            calib_384well = load_config_file(calib_temp_path)
            if calib_384well is not None:
                logging.info(f"Loaded calibration template from {calib_temp_path}")
                return calib_384well
            else:
                logging.warning(f"Failed to load calibration template from {calib_temp_path}")
        
        logging.info("No template found, performing manual calibration")
        calib_384well = self._calibrate_dish_manual(nikon)
        save_config_file(self.calib_path, calib_384well)
        return calib_384well
    
    def _calibrate_dish_manual(self, nikon: NikonTi2)-> dict[str, WellSquareCoord]: # type: ignore[override]
        """
        Calibrates the 384-well plate by calculating the exact step size (pitch) 
        between the top-left corner of A1 and the top-left corner of P24.
        """
        
        # 1. Fetch both manual top-left coordinates directly from stage positioning
        x_tl_a1, y_tl_a1 = prompt_for_top_left_A1(nikon)
        x_tl_p24, y_tl_p24 = prompt_for_top_left_P24(nikon)
        
        
        
        # 2. Compute true physical distances spanning across the grid
        # 23 column transitions from index 0 to 23; 15 row transitions from 0 to 15
        total_span_x = x_tl_p24 - x_tl_a1
        total_span_y = y_tl_p24 - y_tl_a1
        
        # 3. Derive exact step dimensions per cell (pitch = well dimension + gap)
        pitch_x = total_span_x / (self.col_number - 1)
        pitch_y = total_span_y / (self.row_number - 1)
        
        # 4. Establish bottom-right offsets relative to local top-left settings.
        # Based on your physical tracking vector: X steps left (negative value), Y steps down (positive value).
        # We determine the sign of the individual well vector using the total scale orientation.
        well_vector_x = self.well_length if pitch_x >= 0 else -self.well_length
        well_vector_y = self.well_width if pitch_y >= 0 else -self.well_width
        
        # Create wells grid
        dish_measurements: dict[str, WellSquareCoord] = {}
        for i, letter in enumerate(ascii_uppercase[:self.row_number]):
            for j in range(self.col_number):
                well_number = j + 1
                
                # Linearly interpolate the top-left coordinate for each well
                well_x_tl = x_tl_a1 + (pitch_x * j)
                well_y_tl = y_tl_a1 + (pitch_y * i)
                
                # Shift by the standard physical size to find the local well's bottom-right bounds
                well_x_br = well_x_tl + well_vector_x
                well_y_br = well_y_tl + well_vector_y
                
                dish_measurements[f"{letter}{well_number}"] = WellSquareCoord(
                    top_left=(well_x_tl, well_y_tl), 
                    bottom_right=(well_x_br, well_y_br)
                )
                
        logging.info("2-point top-left calibration completed successfully!")
        return dish_measurements


if __name__ == "__main__":
    # Example usage

    from a1_manager import A1Manager, StageCoord
    a1_manager = A1Manager(objective='20x', lamp_name='pE-800')
    core = a1_manager.core
    nikon = NikonTi2(core = core, objective = '20x')
    calib_name = f"calib_384well.json"
    calib_temp_path = CONFIG_DIR.joinpath(calib_name)
    dish_calibrator = Dish384Well(calib_path=calib_temp_path)
    calibration_data = dish_calibrator._calibrate_dish(nikon)
    print(calibration_data["P24"].top_left[0])  # Print the calibration data for well A1
    print(calibration_data["A1"].bottom_right)  # Print the calibration data for well P24
    
    
    # from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
    # arm = MarZ(core=core, dish='384well')
    
    # import time
    
    # a1_manager.set_stage_position(StageCoord(xy=[calibration_data["P24"].top_left[0], calibration_data["P24"].top_left[1]]))  
    a1_manager.set_stage_position(StageCoord(xy=[calibration_data["A1"].bottom_right[0], calibration_data["A1"].bottom_right[1]]))  
    
    # arm.to_home()  # Move the arm to the home position
    # print(arm._get_arm_position)  # Print the current arm position
        
    # arm.to_liquid()  # Move the arm to the liquid position
  
    # time.sleep(2)  # Wait for 2 seconds
    # print(arm._get_arm_position)  # Print the current arm position
    # arm.to_home()  # Move the arm to the home position
    
  
    
    # # get all the keys in the calibration data
    # well_keys = list(calibration_data.keys())
    # # go through all the wells and print their center coordinates
    # for well in well_keys:
    #     center = calibration_data[well].center
    #     print(f"Well {well}: Center coordinates: {center}")
    
    #     a1_manager.set_stage_position(StageCoord(xy=[calibration_data[well].center[0], calibration_data[well].center[1]]))  
    
    #     arm.to_home()  # Move the arm to the home position
    #     print(arm._get_arm_position)  # Print the current arm position
        
    #     arm.to_liquid()  # Move the arm to the liquid position
  
    #     time.sleep(2)  # Wait for 2 seconds
    #     print(arm._get_arm_position)  # Print the current arm position
    #     arm.to_home()  # Move the arm to the home position