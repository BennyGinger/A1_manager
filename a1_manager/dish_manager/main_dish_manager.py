from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
from pathlib import Path
import logging

from a1_manager.autofocus_main import run_autofocus
from a1_manager import CONFIG_DIR
from a1_manager.utils.utils import save_json, load_json
from a1_manager.dish_manager.well_grid_manager import WellGridManager
from a1_manager.a1manager import A1Manager
from a1_manager.utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord
from a1_manager.dish_manager.dish_calib_manager import DishCalibManager

# Initialize logging
logger = logging.getLogger(__name__)


@dataclass
class DishManager:
    """
    Main class to manage the calibration and grid creation of a dish.
    
    Attributes:
    - dish_name (str): Identifier for the dish type (e.g., '35mm', '96well', 'ibidi-8well').
    - run_dir (Path): Path to the directory where the calibration files will be stored.
    - a1_manager (A1Manager): Instance of the A1Manager class.
    - config_path (Path): Path to the configuration directory.
    - calib_path (Path): Path to the calibration file.
    - dish_calibration (dict[str, WellCircleCoord | WellSquareCoord]): Dictionary mapping well names to their corresponding calibration coordinates.
    """
    
    dish_name: str
    run_dir: Path
    a1_manager: A1Manager
    config_path: Path = field(init=False)
    calib_path: Path = field(init=False)
    dish_calibration: dict[str, WellCircleCoord | WellSquareCoord] = field(init=False)
    
    def __post_init__(self) -> None:
        """Set the path to the calibration file."""
        
        # Create the config path and directory
        self.config_path = self.run_dir.joinpath("config")
        self.config_path.mkdir(exist_ok=True)
        
        # Set the calibration path
        calib_name = f"calib_{self.dish_name}.json"
        self.calib_path = self.config_path.joinpath(calib_name)
        
        # Copy the 96well calibration template file into the run directory
        if self.dish_name == "96well":
            calib_temp_path = CONFIG_DIR.joinpath(calib_name)
            calib_96well: dict[str, WellCircleCoord | WellSquareCoord] = load_json(calib_temp_path)
            save_json(self.calib_path, calib_96well)

    def calibrate_dish(self, well_selection: list[str], overwrite: bool = False) -> dict[str, WellCircleCoord | WellSquareCoord]:
        """
        Calibrate the dish with the specified dish name.
        The calibration measurements are saved in a json file in the run directory, except for the 96well dish where the calibration measurements are pre-defined.
        """
        
        # Initialize the dish calibration manager
        dish = DishCalibManager.dish_calib_factory(self.dish_name, self.calib_path)
        
        # Get the calibration measurements or calibrate the dish
        self.dish_calibration = dish.calibrate_dish(self.a1_manager.nikon, well_selection, overwrite)
        save_json(self.calib_path, self.dish_calibration)
        return self.dish_calibration
    
    def autofocus_dish(self, method: str, overwrite: bool, af_savedir: Path=None) -> None:
        """
        Run autofocus for the dish_calibration in each well.
        The autofocus measurements are saved in the same calibration file.
        """
        return run_autofocus(method, self.a1_manager, self.calib_path, overwrite, af_savedir)
    
    def create_well_grids(self, dmd_window_only: bool, numb_field_view: int=None, overlap_percent: int=None, n_corners_in: int=4) -> dict[str, dict[int, StageCoord]]:
        """
        Create a well grid for a dish, where each well is a dictionary containing the coordinates of all the field of views.
        """
        # Update overlap
        if numb_field_view is not None:
            overlap_percent = None 
        overlap_deci = None
        if overlap_percent is not None:
            overlap_deci = overlap_percent / 100 # Convert from % to decimal
        
        # Initialize the well grid manager
        well_grid_manager = WellGridManager.load_subclass_instance(self.dish_name, dmd_window_only, self.a1_manager)
        
        # Create the well grid
        logger.info(f"{overlap_percent=} and {overlap_deci=}")
        dish_grids: dict[str, dict[int, StageCoord]] = {}
        for well, well_coord in self.dish_calibration.items():
            dish_grids[well] = well_grid_manager.create_well_grid(well_coord, numb_field_view, overlap_deci, n_corners_in)
        
        # Save the dish grids
        dish_grids_name = f"grid_{self.dish_name}.json"
        grids_path = self.config_path.joinpath(dish_grids_name)
        save_json(grids_path, dish_grids)
        return dish_grids
