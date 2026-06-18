from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
from string import ascii_uppercase
import logging

from a1_manager import CONFIG_DIR
from a1_manager.microscope_hardware.nikon import NikonTi2
from a1_manager.dish_manager.dish_calib_manager import DishCalibManager
from a1_manager.dish_manager.dish_utils.prompt_utils import prompt_for_center
from a1_manager.utils.utility_classes import WellSquareCoord
from a1_manager.utils.json_utils import load_config_file, save_config_file


SETTINGS_384WELL = {
    'row_number': 16,
    'col_number': 24,
    'length': 127.76 * 1000, # in micron
    'width': 85.48 * 1000, # in micron
    'well_length': 2.5 * 1000, # in micron
    'well_width': 2.5 * 1000, # in micron
    'well_gap_length': 2.0 * 1000, # in micron
    'well_gap_width': 2.0 *1000 # in micron
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
        Try to load the calibration template for the 384-well plate from the config directory. If not found, perform manual calibration.
        Returns a dictionary mapping well names (e.g., 'A1', 'B2', etc.) to WellCircle objects.
        """
        # Try to load from template
        calib_name = f"calib_384well.json"
        calib_temp_path = CONFIG_DIR.joinpath(calib_name)
        if calib_temp_path.exists():
            calib_384well = load_config_file(calib_temp_path)
            if calib_384well is not None:
                logging.info(f"Loaded calibration template from {calib_temp_path}")
                return calib_384well  # Return directly, don't save here
            else:
                logging.warning(f"Failed to load calibration template from {calib_temp_path}")
        
        # Fall back to manual calibration
        logging.info("No template found, performing manual calibration")
        calib_384well = self._calibrate_dish_manual(nikon)
        save_config_file(self.calib_path, calib_384well)
    
    def _calibrate_dish_manual(self, nikon: NikonTi2)-> dict[str, WellSquareCoord]: # type: ignore[override]
        """
        Calibrates the 384-well plate by computing each well's top-left and bottom-right corners.
        If the top-left center is not provided, the user is prompted to move to the A1 well.
        Returns a dictionary mapping well names (e.g., 'A1', 'B2', etc.) to WellSquareCoord objects.
        """
        
        # Prompt the user to move the stage to the center of the A1 well
        x_center, y_center = prompt_for_center(nikon)
        
        # Calculate the top-left and bottom-right corners for well A1.
        x_tl = x_center + self.well_length / 2
        y_tl = y_center - self.well_width / 2
        x_br = x_center - self.well_length / 2
        y_br = y_center + self.well_width / 2
        
        # Create wells
        dish_measurements: dict[str, WellSquareCoord] = {}
        for i, letter in enumerate(ascii_uppercase[:self.row_number]):
            for j in range(self.col_number):
                well_number = j + 1
                
                well_x_tl = x_tl - (self.well_length + self.well_gap_length) * j
                well_y_tl = y_tl + (self.well_width + self.well_gap_width) * i
                well_x_br = x_br - (self.well_length + self.well_gap_length) * j
                well_y_br = y_br + (self.well_width + self.well_gap_width) * i
                
                # Save the well
                dish_measurements[f"{letter}{well_number}"] = WellSquareCoord(
                    top_left=(well_x_tl, well_y_tl), 
                    bottom_right=(well_x_br, well_y_br)
                    )
        logging.info("Calibration successful for 384-well plate!")
        return dish_measurements
    
    def _calibrate_dish_manual_2(self, nikon: NikonTi2) -> dict[str, WellSquareCoord]:
        """
            Calibrates the plate using 3 corner wells to calculate true grid rotation 
            and scaling, preventing center drift at the edges (e.g., P24).
        """
        logging.info("--- Starting Drift-Corrected 3-Point Calibration ---")
        
        # 1. Manually find the true centers of the 3 corner points using the joystick
        print("Please center the joystick precisely on Well A1.")
        a1_x, a1_y = prompt_for_center(nikon)
        
        print("Please drive to and center precisely on Well A24 (Top Right Corner).")
        a24_x, a24_y = prompt_for_center(nikon)
        
        print("Please drive to and center precisely on Well P1 (Bottom Left Corner).")
        p1_x, p1_y = prompt_for_center(nikon)
        
        # 2. Calculate the exact physical step vectors directly from your stage data
        # This automatically captures any rotation skew or scaling errors!
        total_cols = self.col_number - 1 # 23 steps from col 1 to 24
        total_rows = self.row_number - 1 # 15 steps from row A to P
        
        # How much the stage ACTUALLY shifts per column step
        x_step_per_col = (a24_x - a1_x) / total_cols
        y_skew_per_col = (a24_y - a1_y) / total_cols # Usually near 0, handles rotation
        
        # How much the stage ACTUALLY shifts per row step
        x_skew_per_row = (p1_x - a1_x) / total_rows  # Usually near 0, handles rotation
        y_step_per_row = (p1_y - a1_y) / total_rows
        
        dish_measurements: dict[str, WellSquareCoord] = {}
        
        # 3. Generate the drift-free coordinate grid
        for i, letter in enumerate(ascii_uppercase[:self.row_number]):
            for j in range(self.col_number):
                well_number = j + 1
                
                # Compute the precise mathematical center for this specific well
                well_x_center = a1_x + (x_step_per_col * j) + (x_skew_per_row * i)
                well_y_center = a1_y + (y_skew_per_col * j) + (y_step_per_row * i)
                
                # Calculate the boundaries relative to this true center
                well_x_tl = well_x_center + (self.well_length / 2)
                well_y_tl = well_y_center - (self.well_width / 2)
                well_x_br = well_x_center - (self.well_length / 2)
                well_y_br = well_y_center + (self.well_width / 2)
                
                dish_measurements[f"{letter}{well_number}"] = WellSquareCoord(
                    top_left=(well_x_tl, well_y_tl), 
                    bottom_right=(well_x_br, well_y_br)
                )
                
        logging.info("Drift-corrected calibration successful for 384-well plate!")
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
    print(calibration_data["P24"].center[0])  # Print the calibration data for well A1
    
    
    # from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
    # arm = MarZ(core=core, dish='384well')
    
    # import time
    
    a1_manager.set_stage_position(StageCoord(xy=[calibration_data["A1"].center[0], calibration_data["A1"].center[1]]))  
    
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