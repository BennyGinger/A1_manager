from pathlib import Path
import logging
import itertools
from typing import Any, Callable, Optional

import numpy as np
from numpy.typing import NDArray
from a1_manager.a1manager import A1Manager
from a1_manager.autofocus.af_manager import AutoFocusManager
from a1_manager.autofocus.af_utils import RestartAutofocus, QuitAutofocus
from a1_manager.utils.json_utils import load_config_file, save_config_file
from a1_manager.utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord


logger = logging.getLogger(__name__)

FOCUS_RANGES = {
    'ZDrive': {'small': {'searchRange':  200, 'step':  10},},
    'PFSOffset': {'small': {'searchRange': 1000, 'step': 100},}}


def run_autofocus(method: str, 
                  a1_manager: A1Manager, 
                  calib_path: Path, 
                  overwrite: bool, 
                  af_savedir: Path | None = None,
                  review_callback: Optional[Callable[[NDArray], None]] = None
                  )-> None:
        """
        Run autofocus for the selected wells. Requires the calibration file with the dish measurements.
        Dish measurements are in the form of a dict with well names as keys and dict of {'radius':rad,'center':(x_center, y_center),'ZDrive':None,'PFSOffset':None} as values.
        If the autofocus has failed, the user can restart the process without exiting.
        
        Args:
            method (str): Autofocus method to use. Choose from 'sq_grad', 'OughtaFocus', 'Manual'.
            a1_manager (A1Manager): A1Manager object.
            calib_path (Path): Path to the calibration file.
            overwrite (bool): If True, overwrite the focus values in the calibration file.
            af_savedir (Path): Path to save the images for the square gradient method.
            review_callback (Callable[[NDArray], None] | None): Optional callback to display the autofocus image for user review. If None, a blocking prompt will be used.
        """
        
        # Initialize focus device
        focus_device = str(a1_manager.core.get_property('Core', 'Focus')) # type: ignore
        logger.info(f'Autofocus with {focus_device} using {method} method')
        a1_manager.nikon.select_focus_device(focus_device)
        
        # Switch off DIA light if on
        a1_manager.core.set_property('DiaLamp', 'State', 0) # type: ignore
        
        # Load dish measurements
        dish_measurements = load_config_file(calib_path)
        autofocus = AutoFocusManager(a1_manager, method, af_savedir) 

        sorted_wells = _snake_sort_wells(dish_measurements)
        for idx, (well, measurement) in enumerate(sorted_wells):
            # Skip if no measurement coord
            if measurement[focus_device] is not None and not overwrite:
                logger.info(f"Autofocus already done for {well} with {focus_device} at {measurement[focus_device]}")
                continue
        
            try:
                # Process the well for autofocus
                focus = _focus_one_well(idx=idx,
                                        well=well,
                                        measurement=measurement,
                                        focus_device=focus_device,
                                        autofocus=autofocus,
                                        review_callback=review_callback)

            except QuitAutofocus:
                # Quit the autofocus process - re-raise to propagate to caller
                logger.warning("User quit; propagating QuitAutofocus exception.")
                raise
            
            # Update dish measurements  
            measurement[focus_device] = focus
                
            # Save dish measurements and exit
            save_config_file(calib_path, dish_measurements)
            
        if method == 'Manual':
            logger.info("Autofocus was added mannually for all the wells.")
            
def _focus_one_well(*, idx: int, well: str, measurement: WellCircleCoord | WellSquareCoord, focus_device: str, autofocus: AutoFocusManager, review_callback: Optional[Callable[[NDArray], None]] = None) -> float:
    """
    Process a single well for autofocus.
    Args:
        idx (int): Index of the well in the list of wells.
        well (str): Well name (e.g., 'A1').
        measurement (WellCircleCoord | WellSquareCoord): Measurement data for the well.
        focus_device (str): Focus device to use. Choose from 'ZDrive' or 'PFSOffset'.
        autofocus (AutoFocusManager): AutoFocusManager object.
        review_callback (Callable[[NDArray], None] | None): Optional callback to display the autofocus image for user review. If None, a blocking prompt will be used.
    Returns:
        float: Focus value for the well.
    """
    while True:
        try:
            # Extract manager back
            a1_manager = autofocus.a1_manager

            # Move to center of well
            _move_stage_to_center(idx, well, measurement, a1_manager, autofocus.method)

            # Apply fine focus range
            focus = autofocus.find_focus(**FOCUS_RANGES[focus_device]['small'])

            # If first well, show the image and prompt user
            if idx == 0:
                logger.info(f'Focus value: {focus}')
                img = a1_manager.snap_image()
                _autofocus_review(img, review_callback=review_callback)  # Will use callback if provided, else blocking
            
            if idx != 0 and autofocus.method != 'Manual':
                logger.info(f"Autofocus done for {well} with {focus_device} at {focus}")
            return focus

        except RestartAutofocus:
            # loop back and retry
            logger.info("   ↻ Restarting this well…")

        except QuitAutofocus:
            logger.warning("   ✗ Quit detected in helper; propagating")
            raise QuitAutofocus

def _move_stage_to_center(idx: int, well: str, measurement: WellCircleCoord | WellSquareCoord, a1_manager: A1Manager, method: str) -> None:
    if method == 'Manual' and idx != 0:
        return
    
    if measurement.center is None:
        logger.error(f"Measurement center is None for well {well}. Skipping autofocus for this well.")
        raise ValueError("Measurement center cannot be None.")
    logger.info(f"Autofocus for well {well}")
    point_center = StageCoord(xy=measurement.center)
    a1_manager.nikon.set_stage_position(point_center)

def _autofocus_review(img: NDArray, review_callback: Optional[Callable[[NDArray], None]] = None):
    """
    Review autofocus image. If review_callback is provided, call it (non-blocking, GUI-embedded).
    Otherwise, use the default blocking pop-up/terminal review.
    """
    if review_callback is not None:
        review_callback(img)
        # The pipeline must wait for the result via signal/callback/state machine
    else:
        from a1_manager.autofocus.af_utils import prompt_autofocus_with_image
        prompt_autofocus_with_image(img, use_gui=True)

def _get_well_center(measurement: WellCircleCoord | WellSquareCoord) -> tuple[float, float]:
    # Works for both WellCircleCoord and WellSquareCoord
    return getattr(measurement, 'center', (np.nan, np.nan))

def _snake_sort_wells(dish_measurements: dict[str, WellCircleCoord | WellSquareCoord]) -> list[tuple[str, WellCircleCoord | WellSquareCoord]]:
    wells = [(well, m)
        for well, m in dish_measurements.items()
        if _get_well_center(m) is not None]

    wells.sort(key=lambda item: _get_well_center(item[1])[1])  # sort by y
    rows = []
    for _, group in itertools.groupby(wells, key=lambda item: _get_well_center(item[1])[1]):
        rows.append(list(group))
    sorted_wells = []
    for i, row in enumerate(rows):
        # For even rows (starting from top), left-to-right is descending x
        # For odd rows, right-to-left is ascending x
        reverse = (i % 2 == 0)
        row_sorted = sorted(row, key=lambda item: _get_well_center(item[1])[0], reverse=reverse)
        sorted_wells.extend(row_sorted)
    return sorted_wells