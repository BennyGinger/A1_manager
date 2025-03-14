from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
from pathlib import Path

from autofocus_main import run_autofocus
from utils.utils import find_project_root, save_file, load_file
from dish_manager.well_grid_manager import WellGridManager
from main import A1Manager
from utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord
from dish_manager.dish_calib_manager import DishCalibManager


@dataclass
class DishManager:
    """Main class to manage the calibration and grid creation of a dish.
    
    Attributes:
        dish_name (str): Identifier for the dish type (e.g., '35mm', '96well', 'ibidi-8well').
        
        run_dir (Path): Path to the directory where the calibration files will be stored.
        
        a1_manager (A1Manager): Instance of the A1Manager class.
        
        config_path (Path): Path to the configuration directory.
        
        calib_path (Path): Path to the calibration file.
        
        dish_calibration (dict[str, WellCircleCoord | WellSquareCoord]): Dictionary mapping well names to their corresponding calibration coordinates."""
    
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
            root_path = find_project_root(Path(__file__).resolve()) 
            calib_temp_path = root_path.joinpath("config", calib_name)
            calib_96well: dict[str, WellCircleCoord | WellSquareCoord] = load_file(calib_temp_path)
            save_file(self.calib_path, calib_96well)

    def calibrate_dish(self, well_selection: list[str], overwrite: bool = False) -> dict[str, WellCircleCoord | WellSquareCoord]:
        """Calibrate the dish with the specified dish name. The calibration measurements are saved in a json file in the run directory, except for the 96well dish where the calibration measurements are pre-defined."""
        
        # Initialize the dish calibration manager
        dish = DishCalibManager.dish_calib_factory(self.dish_name, self.calib_path)
        
        # Get the calibration measurements or calibrate the dish
        self.dish_calibration = dish.calibrate_dish(self.a1_manager.nikon, well_selection, overwrite)
        save_file(self.calib_path, self.dish_calibration)
        return self.dish_calibration
    
    def autofocus_dish(self, method: str, overwrite: bool, **kwargs) -> dict[str, WellCircleCoord | WellSquareCoord] | None:
        """Run autofocus for the dish_calibration in each well. The autofocus measurements are saved in the same calibration file."""
        
        af_savedir = kwargs.get('af_savedir', None)
        return run_autofocus(method, self.a1_manager, self.calib_path, overwrite, af_savedir)
    
    def create_well_grids(self, dmd_window_only: bool, numb_field_view: int=None, overlap_percent: int=None, **kwargs) -> dict[str, dict[int, StageCoord]]:
        """Create a well grid for a dish."""
        
        # Update overlap
        if numb_field_view is not None:
                overlap_percent = None # Then the grid will be maximised, i.e. with the optimum overlap
            
        if overlap_percent is not None:
            overlap_deci = overlap_percent / 100 # Convert from % to decimal
        
        # Number of corners in the grid
        n_corners_in = kwargs.get('n_corners_in', 4)
        
        # Initialize the well grid manager
        well_grid_manager = WellGridManager.load_subclass_instance(self.dish_name, dmd_window_only, self.a1_manager)
        
        # Create the well grid
        dish_grids: dict[str, dict[int, StageCoord]] = {}
        for well, well_coord in self.dish_calibration.items():
            dish_grids[well] = well_grid_manager.create_well_grid(well_coord, numb_field_view, overlap_deci, n_corners_in)
        
        # Save the dish grids
        dish_grids_name = f"grid_{self.dish_name}.json"
        grids_path = self.config_path.joinpath(dish_grids_name)
        save_file(grids_path, dish_grids)
        return dish_grids