from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path

from utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord
from main import A1Manager
from dish_manager.main_dish_manager import DishManager


def launch_dish_workflow(dish_name: str, run_dir: Path, a1_manager: A1Manager, well_selection: str | list[str], af_method: str, dmd_window_only: bool, numb_field_view: int=None, overlap_percent: int=None, overwrite_calibration: bool = False, overwrite_autofocus: bool = False, **kwargs) -> tuple[dict[str, WellCircleCoord | WellSquareCoord], dict[str, dict[int, StageCoord]]]:
    """Launch the dish workflow to calibrate the dish, perform autofocus, and create the well grids."""
    
    # Initialize the dish manager
    dish_manager = DishManager(dish_name, run_dir, a1_manager) 
    
    # Calibrate the dish
    dish_manager.calibrate_dish(well_selection, overwrite_calibration)
    
    # Perform autofocus, savedir for the square gradient method is optional and can be passed as a keyword argument
    dish_calibration = dish_manager.autofocus_dish(af_method, overwrite_autofocus, **kwargs)
    
    # Get the grids, n_corners_in is optional and can be passed as a keyword argument
    dish_grids = dish_manager.create_well_grids(dmd_window_only, numb_field_view, overlap_percent, **kwargs)
    return dish_calibration, dish_grids
