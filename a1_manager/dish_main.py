from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path

from a1_manager.utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord
from a1_manager.a1manager import A1Manager
from a1_manager.dish_manager.main_dish_manager import DishManager


def launch_dish_workflow(dish_name: str, run_dir: Path, a1_manager: A1Manager, well_selection: str | list[str], af_method: str, dmd_window_only: bool, numb_field_view: int=None, overlap_percent: int=None, overwrite_calibration: bool = False, overwrite_autofocus: bool = False, **kwargs) -> tuple[dict[str, WellCircleCoord | WellSquareCoord], dict[str, dict[int, StageCoord]]]:
    """
    Launch the dish workflow to calibrate the dish, perform autofocus, and create the well grids.
    Args:
        dish_name (str): Name of the dish. Choose from '96well', '35mm', 'ibidi-8well'
        run_dir (Path): Directory to save the results.
        a1_manager (A1Manager): A1Manager object.
        well_selection (str | list[str]): Well selection for measurement.
        af_method (str): Autofocus method to use. Choose from 'sq_grad', 'OughtaFocus', 'Manual'.
        dmd_window_only (bool): If True, only the DMD window will be used for measurement.
        numb_field_view (int | None): Number of field views to use. If None, the whole well will be used.
        overlap_percent (int | None): Overlap percentage for the field views. If None, optimal overlap will be used.
        overwrite_calibration (bool): If True, overwrite the calibration file.
        overwrite_autofocus (bool): If True, overwrite the autofocus values.
        **kwargs: Additional keyword arguments for the dish manager.
    Returns:
        tuple[dict[str, WellCircleCoord | WellSquareCoord], dict[str, dict[int, StageCoord]]]: 
            - dish_calibration: The updated dish measurements with the focus values.
            - dish_grids: The well grids created for the selected wells.
    """
    
    # Initialize the dish manager
    dish_manager = DishManager(dish_name, run_dir, a1_manager) 
    
    # Calibrate the dish
    dish_manager.calibrate_dish(well_selection, overwrite_calibration)
    
    # Perform autofocus, 'savedir' for the square gradient method is optional and can be passed as a keyword argument
    dish_calibration = dish_manager.autofocus_dish(af_method, overwrite_autofocus, **kwargs)
    
    # Get the grids, n_corners_in is optional and can be passed as a keyword argument
    dish_grids = dish_manager.create_well_grids(dmd_window_only, numb_field_view, overlap_percent, **kwargs)
    return dish_calibration, dish_grids
