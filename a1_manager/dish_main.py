from pathlib import Path

from dish_manager.well_grid_manager import WellGridManager
from main import A1Manager
from utils.utility_classes import WellCircleCoord, WellSquareCoord
from microscope_hardware.nikon import NikonTi2
from dish_manager.dish_calib_manager import DishCalibManager


def calibrate_dish(dish_name: str, run_dir: Path, nikon: NikonTi2, well_selection: list[str], overwrite: bool = False) -> dict[str, WellCircleCoord | WellSquareCoord]:
    """Calibrate the dish with the specified dish name. The calibration measurements are saved in a json file in the run directory, except for the 96well dish where the calibration measurements are pre-defined."""
    
    # Initialize the dish calibration manager
    dish = DishCalibManager.dish_calib_factory(dish_name, run_dir)
    
    # Get the calibration measurements or calibrate the dish
    dish_calibration = dish.calibrate_dish(nikon, well_selection, overwrite)
    return dish_calibration

def create_well_grid(dish_name: str, dmd_window_only: bool, a1_manager: A1Manager, dish_calibration: dict[str, WellCircleCoord | WellSquareCoord], numb_field_view: int=None, overlap_percent: int=None, n_corners_in: int = 4):
    """Create a well grid for a dish."""
    
    # Update overlap
    if numb_field_view is not None:
            overlap_percent = None # Then the grid will be maximised, i.e. with the optimum overlap
        
    if overlap_percent is not None:
        overlap_deci = overlap_percent / 100 # Convert from % to decimal
    
    # Initialize the well grid manager
    well_grid_manager = WellGridManager.load_subclass_instance(dish_name, dmd_window_only, a1_manager)
    
    # Determine the settings for the grid
    well_grid_settings = {'overlap': overlap_deci, 'numb_field_view': numb_field_view}
    if dish_name != 'ibidi-8well':
        well_grid_settings['n_corners_in'] = n_corners_in
    
    # Create the well grid
    dish_grids = {}
    for well, well_coord in dish_calibration.items():
        dish_grids[well] = well_grid_manager.create_well_grid(well_coord, **well_grid_settings)
    
    