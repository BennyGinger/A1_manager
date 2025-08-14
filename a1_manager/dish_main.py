from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path

from a1_manager.utils.utility_classes import StageCoord
from a1_manager.a1manager import A1Manager
from a1_manager.dish_manager.main_dish_manager import DishManager
from a1_manager.autofocus.af_utils import QuitAutofocus


def launch_dish_workflow(a1_manager: A1Manager, 
                         run_dir: Path, 
                         *,
                         dish_name: str, 
                         well_selection: str | list[str], 
                         af_method: str, 
                         dmd_window_only: bool, 
                         numb_field_view: int=None, 
                         overlap_percent: int=None, 
                         overwrite_calib: bool = False, 
                         overwrite_autofocus: bool = False, 
                         af_savedir: Path | None = None,
                         n_corners_in: int = 4
                         ) -> dict[str, dict[int, StageCoord]]:
    """
    Launch the dish workflow to calibrate the dish, perform autofocus, and create the well grids.
    
    Args:
        a1_manager (A1Manager): A1Manager object.
        run_dir (Path): Directory to save the results.
        dish_name (str): Name of the dish. Choose from '96well', '35mm', 'ibidi-8well'
        well_selection (str | list[str]): Well selection for measurement.
        af_method (str): Autofocus method to use. Choose from 'sq_grad', 'OughtaFocus', 'Manual'.
        dmd_window_only (bool): If True, only the DMD window will be used for measurement.
        numb_field_view (int | None): Number of field views to use. If None, the whole well will be used.
        overlap_percent (int | None): Overlap percentage for the field views. If None, optimal overlap will be used.
        overwrite_calibration (bool): If True, overwrite the calibration file.
        overwrite_autofocus (bool): If True, overwrite the autofocus values.
        af_savedir (Path | None): Directory to save the autofocus images. Only applicable for the square gradient method.
        n_corners_in (int, optional): Number of corners of each fov that should be contained within a round well at the edges. Defaults to 4.
    
    Returns:
        dict[str, dict[int, StageCoord]]: Dictionary where each well is a dictionary containing the coordinates of all the field of views.
    """
    
    # Initialize the dish manager
    dish_manager = DishManager(dish_name, run_dir, a1_manager) 
    
    # Calibrate the dish
    dish_manager.calibrate_dish(well_selection, overwrite_calib)
    
    try:
        # Perform autofocus, 'savedir' for the square gradient method is optional and can be passed as a keyword argument
        dish_manager.autofocus_dish(af_method, overwrite_autofocus, af_savedir)
    except QuitAutofocus:
        # User quit during autofocus - propagate the exception to stop the entire pipeline
        raise
    
    # Get the grids, n_corners_in is optional and can be passed as a keyword argument
    return dish_manager.create_well_grids(dmd_window_only, numb_field_view, overlap_percent, n_corners_in)
